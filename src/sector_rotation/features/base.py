from typing import NamedTuple

import pandas as pd


class WeeklyBars(NamedTuple):
    close: pd.DataFrame
    ret_1w: pd.DataFrame


def compute_wk_bars(prices_long, tickers, drop_incomplete=True) -> WeeklyBars:
    """
    Daily long-format prices -> weekly (Friday) bars and 1-week returns.

    Pure: takes a DataFrame, returns DataFrames, touches no database. That is
    what makes it testable - you can feed it a hand-built frame. Input comes
    from db.read_prices; output feeds every feature module.

    Returns a WeeklyBars(close, ret_1w). Both frames share the same index and
    columns, so ret_1w is computed once here rather than separately in vol.py
    and beta.py, where the two could drift apart.

    Steps:
    1. pivot() reshapes long -> wide: the long frame has one row per
       (date, ticker) pair; the wide frame has one row per date and one column
       per ticker, with `value` filling the grid. Missing pairs become NaN.
    2. wide[list(tickers)] reindexes the columns into the order you asked for.
       pivot always returns columns sorted alphabetically, so without this the
       column order would depend on the ticker names. Pinning it keeps
       downstream positional access stable. It also raises KeyError if a
       requested ticker is absent from the data - a loud, early failure.
       sort_index() sorts by date, which .resample() requires.
    3. resample("W-FRI").last() buckets the daily rows into weeks ending Friday
       and takes the last close in each bucket. "W-FRI" labels each bucket with
       its Friday date. .last() takes the last *observed* value in the bucket,
       skipping NaN - so a Thursday close is used if Friday is missing.
    4. Drop the final bar if it is a partial week (see the inline comment).
    5. Three asserts on the index: sorted, no duplicates, every date a Friday
       (dayofweek 4 = Friday, Monday being 0). These are cheap and catch a bad
       resample here rather than three modules downstream.
    6. pct_change(1) on the weekly closes gives each week's return: this week's
       close over last week's, minus 1. Row 0 is always NaN - there is no prior
       week to compare against. fill_method=None for the same reason as in
       momentum.py: no fabricated 0% returns across a ragged start.
    """
    wide = prices_long.pivot(index="date", columns="ticker", values="value")
    # pivot sorts columns alphabetically; reindex to a known order so downstream
    # column positions stay stable. Raises if a requested ticker is missing.
    wide = wide[list(tickers)].sort_index()

    weekly = wide.resample("W-FRI").last()

    if drop_incomplete and len(weekly) and wide.index[-1] < weekly.index[-1]:
        # resample stamps the bucket with its Friday even when the daily data
        # stops mid-week, so that last bar is partial. A Friday market holiday
        # trips this too - we drop it rather than carry a calendar dependency.
        weekly = weekly.iloc[:-1]

    assert weekly.index.is_monotonic_increasing, "weekly index not sorted"
    assert weekly.index.is_unique, "duplicate weekly dates"
    assert (weekly.index.dayofweek == 4).all(), "weekly index has non-Fridays"

    return WeeklyBars(
        close=weekly,
        ret_1w=weekly.pct_change(1, fill_method=None),
    )