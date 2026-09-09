import pandas as pd

from sector_rotation.config import ALL_TICKERS
from sector_rotation.db import get_conn


def load_daily_prices() -> pd.DataFrame:
    """
    Reads the adjusted closes of all 12 Tiingo tickers out of the prices table and returns them with dates down the side and tickers across the top.
    Returns a DataFrame of roughly 7,200 rows by 12 columns; cells before a ticker's first trading day are NaN rather than 0.
    `pivot` turns the long table, which has one row per date-and-ticker pair, into the wide shape where each ticker gets its own column.
    """

    # Build one "?" placeholder per ticker so the ticker list can be passed as query parameters instead of pasted into the SQL string
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

    # Reorder the columns to match ALL_TICKERS so the order comes from config rather than landing alphabetically
    # XLRE and XLC list later than the rest, so their early cells stay NaN here and are never filled with 0 - a 0 would read as a real price and produce a fabricated return.
    return wide[ALL_TICKERS]


def to_weekly(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Resamples a daily price frame down to one row per week, labeled with that week's Friday and holding the last close in the week.
    Returns a DataFrame of roughly 1,450 rows by 12 columns, with the final row dropped when the week it labels has not finished.
    `resample("W-FRI").last()` groups the rows into weeks ending on Friday and keeps the last non-null value in each group.
    """

    # Group the daily rows into weeks ending Friday and keep each week's last close
    weekly = daily.resample("W-FRI").last()

    # If the last row's Friday is not a date that exists in the daily data, drop that row
    # Resample labels an unfinished week with its upcoming Friday and fills it with whatever close is available, so a Wednesday run would produce a row whose lookback windows are 2 days short.
    # Known limitation: when that Friday is a market holiday, such as Good Friday, the date never exists in the data and a genuinely finished week gets dropped. That costs one week of signal at most once or twice a year, and it errs toward discarding a usable week rather than admitting an unusable one.
    if len(weekly) and weekly.index[-1] not in daily.index:
        weekly = weekly.iloc[:-1]

    return weekly
