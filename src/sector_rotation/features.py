from collections.abc import Sequence

import pandas as pd

from sector_rotation.config import ALL_TICKERS, SECTORS
from sector_rotation.db import get_conn

# The 3 momentum lookbacks in weeks: 4 for recent strength, 12 for the classic horizon, 26 for the slower trend.
MOMENTUM_WINDOWS: tuple[int, ...] = (4, 12, 26)

# The 2 volatility lookbacks in trading days, roughly 1 month and 3 months. Measured on daily returns rather than weekly ones so each estimate rests on 20 or 60 observations instead of 4 or 12.
VOLATILITY_WINDOWS: tuple[int, ...] = (20, 60)


def load_daily_prices() -> pd.DataFrame:
    """
    Reads the adjusted closes of all 12 Tiingo tickers out of the prices table and returns them with dates down the side and tickers across the top.
    Returns a DataFrame of roughly 7,200 rows by 12 columns; cells before a ticker's first trading day are NaN rather than 0.
    `pivot` turns the long table, which has one row per date-and-ticker pair, into the wide shape where each ticker gets its own column.
    """

    placeholders = ",".join("?" * len(ALL_TICKERS))

    # Open the database connection, read the 12 tickers into a long dataframe with real dates, close the connection
    conn = get_conn()
    long = pd.read_sql(
        f"SELECT date, ticker, value FROM prices WHERE ticker IN ({placeholders}) ORDER BY date, ticker",
        conn,
        params=ALL_TICKERS,
        parse_dates=["date"],
    )
    conn.close()

    # Reshape from one row per date-and-ticker into one row per date with a column per ticker
    wide = long.pivot(index="date", columns="ticker", values="value")

    # Reorder the columns to match ALL_TICKERS, XLRE and XLC list later than the rest
    return wide[ALL_TICKERS]


def to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Resamples a daily price frame down to one row per week, labeled with that week's Friday and holding the last close in the week.
    Returns a DataFrame of roughly 1,450 rows by 12 columns, with the final row dropped when the week it labels has not finished.
    `resample("W-FRI").last()` groups the rows into weeks ending on Friday and keeps the last non-null value in each group.
    """

    # Group the daily rows into weeks ending Friday and keep each week's last close
    weekly = daily.resample("W-FRI").last()

    # If the last friday of the week in unavailiable, drop the week
    if len(weekly) and weekly.index[-1] not in daily.index:
        weekly = weekly.iloc[:-1]

    return weekly


def relative_momentum(
    weekly: pd.DataFrame,
    windows: Sequence[int] = MOMENTUM_WINDOWS,
) -> dict[int, pd.DataFrame]:
    """
    Computes each sector's trailing return minus SPY's return over the same weeks, for every window given.
    Returns a dict keyed by window length, each value a DataFrame of weeks by the 11 sectors; rows before a sector has `window` weeks of history are NaN.
    `sub(series, axis=0)` subtracts one column from every column of the frame, matching them up row by row.
    """

    result: dict[int, pd.DataFrame] = {}

    for window in windows:
        # Divide each week's close by the close `window` weeks earlier and subtract 1, giving every ticker its trailing return
        # fill_method=None turns off pandas' default forward-fill. XLRE and XLC have no prices before they listed, and with filling on pandas would copy their first real price backward and report a fabricated 0% return.
        returns = weekly.pct_change(window, fill_method=None)

        # Subtract SPY's return for that week from every ticker's return for that week
        # SPY's own column becomes exactly 0 here, since it is SPY minus SPY. That is worth checking as proof the rows lined up, and it is why SPY is dropped on the next line.
        relative = returns.sub(returns["SPY"], axis=0)

        # Keep only the 11 sectors, dropping the all-zero SPY column
        # Leaving SPY in would make the task 3 rank run 1 to 12 and put SPY in the portfolio.
        result[window] = relative[SECTORS]

    return result


def momentum_rank(momentum: pd.DataFrame) -> pd.DataFrame:
    """
    Ranks the sectors against each other within each week, giving rank 1 to the strongest.
    Returns a DataFrame the same shape as the input, holding whole numbers 1 through however many sectors have a value that week, and NaN wherever the input was NaN.
    `rank(axis=1)` ranks across each row rather than down each column, so every week is ranked on its own.
    """

    # Rank each week's sectors from strongest to weakest, leaving a sector out of the ranking entirely when it has no momentum value that week
    # NaN cells stay NaN and are not counted, so a week where only 9 sectors have 12 weeks of history ranks them 1 through 9 - that is the "use only the sectors valid that week" rule, with nothing to write.
    # method="first" breaks ties by column order so the output is always whole numbers 1 through n. The default averages ties into values like 3.5, which would break the promise that this column holds integers.
    return momentum.rank(axis=1, ascending=False, method="first")


def realized_volatility(
    daily: pd.DataFrame,
    weekly_index: pd.DatetimeIndex,
    windows: Sequence[int] = VOLATILITY_WINDOWS,
) -> dict[int, pd.DataFrame]:
    """
    Measures how much each sector's daily price has moved around over the trailing window, then reads that number off at each Friday.
    Returns a dict keyed by window length in trading days, each value a DataFrame of weeks by the 11 sectors; weeks before a sector has a full window of returns are NaN.
    `rolling(window).std()` slides a fixed-length window down the rows and takes the standard deviation inside each one, and `reindex(..., method="ffill")` picks the last value on or before each target date.
    """

    # Divide each day's close by the previous day's and subtract 1, giving every ticker its daily return
    # fill_method=None keeps XLRE's and XLC's pre-listing cells as NaN instead of fabricating 0% days that would drag the standard deviation down.
    returns = daily.pct_change(fill_method=None)

    result: dict[int, pd.DataFrame] = {}

    for window in windows:
        # Slide a window of `window` trading days down the returns and take the standard deviation inside each one
        # Rolling defaults to requiring the window to be completely full, so a sector gets no value until it has all 20 or all 60 returns. Not annualized: multiplying by the square root of 252 is the same constant everywhere and changes no ordering a tree could split on.
        rolling_std = returns.rolling(window).std()

        # Pull out the value as of each Friday, taking the last value on or before that date
        # Taking the Friday dates directly would return nothing for a week whose Friday was a market holiday, since Good Friday never appears in the daily index. Reading the last value on or before it gives Thursday's number, which is the last thing the market actually said.
        at_fridays = rolling_std.reindex(weekly_index, method="ffill")

        # Keep only the 11 sectors, dropping SPY
        # Volatility is a sector-specific column, and SPY's own volatility is not one of the 11 features.
        result[window] = at_fridays[SECTORS]

    return result
