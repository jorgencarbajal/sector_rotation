from collections.abc import Sequence

import pandas as pd

from sector_rotation.config import ALL_TICKERS, SECTORS
from sector_rotation.db import get_conn

# The 3 momentum lookbacks in weeks: 4 for recent strength, 12 for the classic horizon, 26 for the slower trend.
MOMENTUM_WINDOWS: tuple[int, ...] = (4, 12, 26)


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
