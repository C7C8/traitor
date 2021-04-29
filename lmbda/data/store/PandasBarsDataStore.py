#  This file is part of traitor.
#
#  traitor is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  traitor is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with traitor.  If not, see <https://www.gnu.org/licenses/>.
#
import datetime
import logging
import shutil
from abc import ABC
from logging import info, warn
from pathlib import Path
from typing import Dict, Set

import pandas as pd
import pytz
from alpaca_trade_api.rest import TimeFrame

from lmbda.data.store import BarsDataStore


class PandasBarsDataStore(BarsDataStore, ABC):
	"""Data store that stores data in a provided folder, in the form of bz2 daily dataframes.
	Dataframes are stored in a hierarchy of data_dir/symbol/[YEAR].pkl.gz """

	def __init__(self, timeframe: TimeFrame, data_dir: str):
		super().__init__(timeframe)
		info(f"Initializing new daily datastore on a {timeframe} timeframe at {data_dir}")
		self.data_dir = Path(data_dir).resolve()
		self.data_dir.mkdir(exist_ok=True)

	def __contains__(self, symbol: str) -> bool:
		return len(list((self.data_dir / symbol.upper()).rglob("*.pkl.gz"))) > 0

	def symbols(self) -> Set[str]:
		return {str(path).split("/")[-2] for path in self.data_dir.rglob("*.pkl.gz")}

	def bars(self, symbol: str, start: datetime.date = None,
	         end: datetime.date = None) -> pd.DataFrame:
		symbol = symbol.upper()
		info(f"Retrieving stored bars for {symbol} from {start} to {end}")
		df_paths = list((self.data_dir / symbol.upper()).glob("*.pkl.gz"))
		if start is None and end is not None:
			# Get all data *except* after the current year
			df_paths = list(filter(lambda path: int(path.name.split(".")[0]) <= end.year, df_paths))
		elif start is not None and end is None:
			df_paths = list(filter(lambda path: int(path.name.split(".")[0]) >= start.year, df_paths))
		elif start is not None and end is not None:
			df_paths = list(filter(lambda path: start.year <= int(path.name.split(".")[0]) <= end.year, df_paths))

		df = pd.concat([pd.read_pickle(path) for path in df_paths])
		if start is None and end is not None:
			df = df[df.index.to_series().dt.date <= end]
		elif start is not None and end is None:
			df = df[df.index.to_series().dt.date >= start]
		elif start is not None and end is not None:
			df = df[(start <= df.index.to_series().dt.date) & (df.index.to_series().dt.date <= end)]
		df.sort_index(inplace=True)
		return df

	def remove(self, symbol: str) -> None:
		warn(f"Deleting all data for {symbol}")
		symbol = symbol.upper()
		if symbol not in self:
			raise ValueError(f"Symbol {symbol} not found in store")
		shutil.rmtree(self.data_dir / symbol)

	def last(self, symbol: str) -> pd.DataFrame:
		# Get the the most current year's dataframe, then get its last row
		symbol = symbol.upper()
		if symbol not in self:
			raise ValueError(f"Symbol {symbol} not found in store")
		df: pd.DataFrame = pd.read_pickle(
			sorted((self.data_dir / symbol.upper()).glob("*.pkl.gz"), key=lambda path: str(path))[-1])
		df.sort_index(inplace=True)
		return df.tail(n=1)

	def update(self, symbol: str, data: pd.DataFrame) -> None:
		symbol = symbol.upper()
		info(f"Updating symbol {symbol} with {len(data)} potentially new rows")
		if symbol not in self:
			raise ValueError(f"Symbol {symbol} not found in store")

		data.sort_index(inplace=True)

		# Get the first and last data points, then load in the dataframes for the corresponding years
		start: pd.Timestamp = data.head(n=1).index.to_series()[0]
		end: pd.Timestamp = data.tail(n=1).index.to_series()[0]
		df_paths = list(filter(lambda path: start.year <= int(path.name.split(".")[0]) <= end.year,
		                       list((self.data_dir / symbol.upper()).glob("*.pkl.gz"))))
		df = pd.concat([pd.read_pickle(path) for path in df_paths])

		# Add the new data and sort. This overrides duplicates.
		if len(df) > 0:
			df = pd.concat([df, data])
			df = df[~df.index.duplicated(keep="last")]
		else:
			df = data
		df.sort_index(inplace=True)

		# Delete the old dataframes and save the new dataframes
		for path in df_paths:
			path.unlink()
		self._save_in_year_chunks(symbol, df)

	def get_out_of_date_symbols(self, threshold: datetime.timedelta = datetime.timedelta(days=3)) -> Dict[
		str, datetime.timedelta]:
		# Get a list of all symbols and map it to a list of all the most recent data points
		last_data_points: Dict[str, pd.DataFrame] = {symbol: self.last(symbol) for symbol in
		                                             self.symbols()}
		out_of_date_symbols: Dict[str, datetime.timedelta] = {}
		now = pd.Timestamp("now", tz=pytz.utc)
		for symbol, data in last_data_points.items():
			if now - data.index.to_series()[0] > threshold:
				out_of_date_symbols[symbol] = now - data.index.to_series()[0]
		return out_of_date_symbols

	def add(self, symbol: str) -> pd.DataFrame:
		symbol = symbol.upper()
		if symbol in self:
			raise ValueError(f"Attempting to add duplicate symbol {symbol}, use flush_updates or update_symbol data instead")
		info(f"Adding {symbol} to store")
		data = self._fetch_all_symbol_history(symbol)
		self._save_in_year_chunks(symbol, data)
		return data

	def _save_in_year_chunks(self, symbol: str, data: pd.DataFrame):
		"""Save a dataframe under a given symbol in year-size chunks"""
		symbol = symbol.upper()
		basepath = self.data_dir / symbol
		basepath.mkdir(exist_ok=True)
		for year, df in data.groupby(data.index.year):
			path = basepath / f"{year}.pkl.gz"
			df.to_pickle(str(path))


if __name__ == '__main__':
	logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
	store = PandasBarsDataStore(TimeFrame.Day, Path("data/history/daily"))

	print("Last GME data point:")
	print(store.last("gme"))

	print(f"All stored symbols: {store.symbols()}")

	out_of_date = store.get_out_of_date_symbols()
	print(f"Out of date symbols: {out_of_date}")

	print("Updating symbols...")
	store.flush_updates(set(out_of_date.keys()))

	print("Adding VOO")
	store.add("VOO")
