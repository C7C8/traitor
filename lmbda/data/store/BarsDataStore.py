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
import abc
import datetime
from logging import info
from typing import Dict, Set

import pandas as pd
import pytz
from alpaca_trade_api.rest import TimeFrame, REST

from .api_client import uses_alpaca_client

class BarsDataStore(metaclass=abc.ABCMeta):
	"""Interface for a bars datastore that's capable of holding data in different backings"""

	def __init__(self, timeframe: TimeFrame):
		self.timeframe = timeframe

	@uses_alpaca_client
	def _fetch_all_symbol_history(self, symbol: str, client: REST, delta=datetime.timedelta(days=(365 * 5))) -> pd.DataFrame:
		end = datetime.date.today() - datetime.timedelta(days=1)
		start = end - delta
		info(f"Fetching all available history for symbol {symbol} from {start} to {end}")
		return client.get_bars(symbol, self.timeframe, str(start), str(end)).df

	@abc.abstractmethod
	def __contains__(self, symbol: str) -> bool:
		"""Returns whether or not data for a given symbol is contained within the store"""
		raise NotImplementedError

	def __getitem__(self, symbol: str) -> pd.DataFrame:
		"""Get all data for a particular symbol"""
		return self.get_bars_from_range(symbol)

	def __setitem__(self, symbol: str, data: pd.DataFrame):
		"""Update store with provided data"""
		self.update_symbol_data(symbol, data)

	def __delete__(self, symbol: str) -> None:
		"""Delete all data for the given symbol"""
		self.delete_symbol_data(symbol)

	@abc.abstractmethod
	def get_all_stored_symbols(self) -> Set[str]:
		"""Get a list of all symbols currently stored"""
		raise NotImplementedError

	@abc.abstractmethod
	def get_bars_from_range(self, symbol: str, start: datetime.date = None,
	                        end: datetime.date = None) -> pd.DataFrame:
		"""Retrieve bars from the given date range. Returns all data if no range is provided. Only queries locally
		cached data. If start is provided but end is not, returns all data until start, and vice versa."""
		raise NotImplementedError

	@abc.abstractmethod
	def get_last_data_point(self, symbol: str) -> pd.DataFrame:
		"""Get the last data point in the store for the given symbol"""
		raise NotImplementedError

	@abc.abstractmethod
	def update_symbol_data(self, symbol: str, data: pd.DataFrame) -> None:
		"""Update the store data for the given symbol with the provided data"""
		raise NotImplementedError

	@abc.abstractmethod
	def delete_symbol_data(self, symbol: str) -> None:
		"""Delete all data for a symbol"""
		raise NotImplementedError

	@abc.abstractmethod
	def get_out_of_date_symbols(self, threshold: datetime.timedelta = datetime.timedelta(days=3)) -> Dict[
		str, datetime.timedelta]:
		"""Get a list of out-of-date symbols and their datedness, where datedness is determined by the provided
		time delta (default: 3 days)"""
		raise NotImplementedError

	def flush_updates(self, symbols: Set[str]) -> None:
		"""Update the list of given symbols with the latest available data"""
		if any([symbol not in self for symbol in symbols]):
			raise ValueError(f"Symbol list {symbols} contained symbol not already in store")

		now = pd.Timestamp("now", tz=pytz.utc)
		# For each symbol, calculate the time delta and get the most recent
		for symbol in symbols:
			delta: datetime.timedelta = now - self.get_last_data_point(symbol).index.to_series()[0]
			data = self._fetch_all_symbol_history(symbol, delta=delta)
			self.update_symbol_data(symbol, data)

	@abc.abstractmethod
	def add_symbol(self, symbol: str) -> pd.DataFrame:
		"""Add a symbol to the store, querying all available data for it and returning the results."""
		raise NotImplementedError
