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
import functools
from logging import debug
from typing import Callable

from alpaca_trade_api.common import URL
from alpaca_trade_api.rest import REST

APCA_API_BASE_URL = URL("https://api.alpaca.markets")
APCA_API_PAPER_URL = URL("https://paper-api.alpaca.markets")


def uses_alpaca_client(func: Callable, paper_trading: bool = True) -> Callable:
	"""Annotation for any function that needs an Alpaca client"""

	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		debug(f"Generating new Alpaca client for {func.__name__}")
		return func(*args, client=_get_alpaca_client(paper_trading), **kwargs)

	return wrapper


@functools.lru_cache
def _get_alpaca_client(paper_trading: bool = True):
	"""Cacheable helper for getting an alpaca client"""
	return REST(base_url=APCA_API_PAPER_URL if paper_trading else APCA_API_BASE_URL)
