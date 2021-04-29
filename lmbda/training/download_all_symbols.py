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

import argparse
import csv
import logging
from logging import info, warning

from alpaca_trade_api.rest import TimeFrame

from lmbda.data.store.PandasBarsDataStore import PandasBarsDataStore

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description="Downloads 5 year daily historical data for all symbols in a set of CSV files")
	parser.add_argument("-d", "--datastore", type=str, default=".", help="Directory to store data")
	parser.add_argument("files", type=argparse.FileType("r"), nargs="+")
	args = parser.parse_args()
	logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

	store = PandasBarsDataStore(data_dir=args.datastore, timeframe=TimeFrame.Minute)
	for file in args.files:
		info(f"Processing {file.name}")
		reader = csv.DictReader(file)
		for company in reader:
			symbol = company["Symbol"]
			if "^" in symbol or "/" in symbol:
				warning(f"Invalid symbol {symbol}, skipping!")
				continue
			if symbol in store:
				info(f"{symbol} already in store, skipping!")
				continue
			info(f"Downloading historical data for {symbol}")
			try:
				store.add(symbol)
			except:
				warning(f"Failed to download data for {symbol}, skipping!")
				continue
