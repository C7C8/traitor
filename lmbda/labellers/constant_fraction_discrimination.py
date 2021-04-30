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
from datetime import timedelta
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import zscore


def perform_cfd(df: pd.DataFrame,
                edge_width: timedelta,
                back_history: int=0,
                pct_change_threshold=0.05,
                outlier_zscore_threshold=3.0
                ) -> List[Tuple[float, List[float]]]:
    """
    Perform constant fraction discrimination to find rising & falling edges
    :param df: Dataframe of stock closing prices
    :param edge_width: Edge width to consider when doing constant fraction discrimination
    :param back_history: Days of back-history to include in the returned datafraem
    :param pct_change_threshold: Absolute percent change required to be considered a viable edge
    :param outlier_zscore_threshold: Z-score threshold for filtering outliers
    :return: A dataframe mapping percent changes to days of history leading up to them."""

    cfd = df["close"]\
        .to_frame()\
        .rename({"close": "delayed"}, axis=1)\
        .shift(freq=edge_width)\
        .join(-df["close"]
              .to_frame()
              .rename({"close": "inverse"}, axis=1), on="timestamp", how="inner")\
        .dropna(axis=0)

    cfd_results = cfd["delayed"] + cfd["inverse"]
    crossings = np.asarray(np.where(np.diff(np.sign(cfd_results))))[0]
    del cfd
    del cfd_results

    df_deltas = pd.DataFrame({
        "idx": crossings,
        "start": df.iloc[crossings]["close"].array,
        "end": df.iloc[crossings + 1]["close"].array
    }, index=df.iloc[crossings].index).dropna().iloc[1:]
    del crossings

    df_deltas["diff"] = df_deltas.start - df_deltas.end
    df_deltas["pct_diff"] = 100.0 * df_deltas["diff"] / df_deltas.start
    df_deltas = df_deltas[(np.abs(zscore(df_deltas.pct_diff)) < outlier_zscore_threshold)
                          & (df_deltas.pct_diff.abs() >= pct_change_threshold)]

    trailing_histories: List[Tuple[float, List[float]]] = []
    for index, row in df_deltas.iterrows():
        if row.idx - 1 - back_history < 0 or row.idx + 1 > len(df):
            continue
        slice_start = int(row.idx - 1 - back_history)
        slice_end = int(row.idx) + 1
        trailing_histories.append((row.pct_diff, list(df.iloc[slice_start:slice_end]["close"].array)))
    return list(filter(lambda history: float('NaN') not in history[1], trailing_histories))
