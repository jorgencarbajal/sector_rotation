from collections.abc import Sequence

import pandas as pd

from sector_rotation.config import ALL_TICKERS, SECTORS
from sector_rotation.db import get_conn

# The 3 momentum lookbacks in weeks: 4 for recent strength, 12 for the classic horizon, 26 for the slower trend.
MOMENTUM_WINDOWS: tuple[int, ...] = (4, 12, 26)

# The 2 volatility lookbacks in trading days, roughly 1 month and 3 months. Measured on daily returns rather than weekly ones so each estimate rests on 20 or 60 observations instead of 4 or 12.
VOLATILITY_WINDOWS: tuple[int, ...] = (20, 60)

# The beta lookback in weeks, 52 being one year of weekly returns.
BETA_WINDOW: int = 52

# The SPY trend lookback in weeks. 40 weeks is roughly the 200-day moving average people quote.
TREND_WINDOW: int = 40

# How many business days to step back from the Friday signal date before reading a FRED series.
# Every FRED series here publishes the prior business day's value: the Treasuries around 4:15pm ET and the credit spread around 10:00am ET. Friday's own values therefore land Monday, after the job has run and after the fill, so Thursday's is the newest one honestly available.
FRED_LAG_BUSINESS_DAYS: int = 1

# The 11 feature columns in the order they are written, after the 3 key columns signal_date, ticker and fill_date.
FEATURE_COLUMNS: tuple[str, ...] = (
    "rel_mom_4w",
    "rel_mom_12w",
    "rel_mom_26w",
    "mom_rank_12w",
    "vol_20d",
    "vol_60d",
    "beta_52w",
    "curve_slope",
    "curve_slope_change",
    "hy_oas",
    "spy_above_40w",
)


def load_daily_prices(tickers: Sequence[str] = ALL_TICKERS) -> pd.DataFrame:
    """
    Reads the given tickers out of the prices table and returns them with dates down the side and tickers across the top.
    Returns a DataFrame with one column per requested ticker; cells before a ticker's first observation are NaN rather than 0.
    `pivot` turns the long table, which has one row per date-and-ticker pair, into the wide shape where each ticker gets its own column.
    """

    # The default reads the 12 Tiingo tickers. Passing FRED_SERIES reads the 3 macro series instead - the reshaping is identical, so a second loader would be a copy of this one.
    tickers = list(tickers)
    placeholders = ",".join("?" * len(tickers))

    # Open the database connection, read the requested tickers into a long dataframe with real dates, close the connection
    conn = get_conn()
    long = pd.read_sql(
        f"SELECT date, ticker, value FROM prices WHERE ticker IN ({placeholders}) ORDER BY date, ticker",
        conn,
        params=tickers,
        parse_dates=["date"],
    )
    conn.close()

    # Reshape from one row per date-and-ticker into one row per date with a column per ticker
    wide = long.pivot(index="date", columns="ticker", values="value")

    # Reorder the columns to match the requested order, XLRE and XLC list later than the rest
    return wide[tickers]


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


def rolling_beta(weekly: pd.DataFrame, window: int = BETA_WINDOW) -> pd.DataFrame:
    """
    Measures how far each sector tends to move when SPY moves, over the trailing `window` weeks.
    Returns a DataFrame of weeks by the 11 sectors holding the slope of the sector's returns against SPY's; weeks before a sector has a full window of returns are NaN.
    `rolling(window).cov(series)` slides a fixed-length window down the rows and takes each column's covariance with that series inside it, and `div(series, axis=0)` divides every column by that series row by row.
    """

    # Divide each week's close by the previous week's and subtract 1, giving every ticker its weekly return, then pull SPY's column out on its own
    returns = weekly.pct_change(fill_method=None)
    spy = returns["SPY"]

    # Slide a window of `window` weeks down the returns, taking each sector's covariance with SPY inside it and SPY's own variance over the same weeks
    # Beta is the slope of the best-fit line through the sector's returns plotted against SPY's, and that slope equals covariance divided by variance, so no regression library is needed.
    covariance = returns.rolling(window).cov(spy)
    spy_variance = spy.rolling(window).var()

    # Divide each sector's covariance by SPY's variance for the same week
    # Both cov and var divide by window minus 1 rather than window, and because it is the same divisor on both sides it cancels here and leaves beta unaffected.
    beta = covariance.div(spy_variance, axis=0)

    # Keep only the 11 sectors, dropping SPY
    # SPY's own column is exactly 1.0 by construction, since covariance with itself over its own variance is 1. That is worth checking as proof the two return series lined up, and it is why the column is dropped rather than kept.
    return beta[SECTORS]


def align_fred(fred_daily: pd.DataFrame, weekly_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Reads each FRED series as of the business day before every Friday signal date, taking the newest observation dated on or before that day.
    Returns a DataFrame with one row per Friday and the same columns as the input; a Friday earlier than the series' first observation is NaN.
    `BDay(n)` shifts a date back by whole business days, and `reindex(..., method="ffill")` picks the last row dated on or before each target date.
    """

    # Step every Friday back one business day, which lands on the Thursday
    lagged_dates = weekly_index - pd.tseries.offsets.BDay(FRED_LAG_BUSINESS_DAYS)

    # Look up the newest observation dated on or before each of those Thursdays
    aligned = fred_daily.reindex(lagged_dates, method="ffill")

    # Put the Friday dates back on the rows so this frame joins against the other features
    aligned.index = weekly_index
    return aligned


def group_b_features(weekly: pd.DataFrame, fred_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the 4 regime columns, which hold the same value for every sector in a given week and matter only through interactions.
    Returns a DataFrame of weeks by 4 columns: curve_slope, curve_slope_change, hy_oas, spy_above_40w.
    `rolling(n).mean()` slides an n-row window down the frame and averages inside it, and `astype("float")` turns the True/False comparison into 1.0 and 0.0.
    """

    # Read the 3 FRED series as of the business day before each Friday
    fred = align_fred(fred_daily, weekly.index)

    # Subtract the 2-year yield from the 10-year to get the curve slope, then take its change from the previous week
    slope = fred["DGS10"] - fred["DGS2"]
    slope_change = slope.diff()

    # Average SPY's weekly close over the trailing 40 weeks and record whether the latest close sits above it
    spy = weekly["SPY"]
    spy_trend = (spy > spy.rolling(TREND_WINDOW).mean()).astype("float")

    # Blank the trend flag for weeks with no 40-week average yet
    # The comparison above turns NaN into False, which would read as a real "below the average" signal for the first 39 weeks rather than as missing data.
    spy_trend[spy.rolling(TREND_WINDOW).mean().isna()] = float("nan")

    return pd.DataFrame(
        {
            "curve_slope": slope,
            "curve_slope_change": slope_change,
            "hy_oas": fred["BAMLH0A0HYM2"],
            "spy_above_40w": spy_trend,
        }
    )


def fill_dates(weekly_index: pd.DatetimeIndex, daily_index: pd.DatetimeIndex) -> pd.Series:
    """
    Finds, for each Friday signal date, the first trading day that comes after it, which is the day that week's trade fills at the open.
    Returns a Series indexed by the Friday dates holding the fill date, or NaT for a Friday with no trading day after it yet.
    `searchsorted(values, side="right")` returns, for each value, the position of the first entry in the index that is strictly greater than it.
    """

    # For each Friday, find the position of the first trading date strictly after it
    # side="right" is what makes it strictly after. side="left" would return the Friday itself whenever the Friday was a trading day, which is filling at Friday's open on a signal from Friday's close.
    # Being strictly after is also what skips holidays without a calendar: Labor Day is simply not in daily_index, so the first date after Friday 2026-09-04 is Tuesday 2026-09-08.
    positions = daily_index.searchsorted(weekly_index, side="right")

    # Turn each position into the date it points at, using NaT where the position runs off the end of the index
    # The newest Friday normally runs off the end, because on a Monday morning the data stops at the previous Friday and the day the trade fills has not been recorded yet. That row still carries usable features; it just has no fill price.
    out = [daily_index[p] if p < len(daily_index) else pd.NaT for p in positions]

    return pd.Series(out, index=weekly_index, name="fill_date")


def build_feature_table(
    weekly: pd.DataFrame,
    daily: pd.DataFrame,
    fred_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    Turns the wide per-feature frames into one long table holding a row for every week and sector, with the 11 features as columns.
    Returns a DataFrame of roughly 15,000 rows by 14 columns, sorted by signal date then ticker; a sector that had no closing price that week gets no row at all.
    `stack(future_stack=True)` folds the sector columns down into rows, turning a weeks-by-sectors frame into one value per week-and-sector pair while keeping the NaN cells.
    """

    # Build each wide feature frame from the price data
    momentum = relative_momentum(weekly)
    volatility = realized_volatility(daily, weekly.index)
    group_a = {
        "rel_mom_4w": momentum[4],
        "rel_mom_12w": momentum[12],
        "rel_mom_26w": momentum[26],
        "mom_rank_12w": momentum_rank(momentum[12]),
        "vol_20d": volatility[20],
        "vol_60d": volatility[60],
        "beta_52w": rolling_beta(weekly),
    }

    # Fold every sector-specific frame from weeks-by-sectors down into one row per week-and-sector pair, then line them up side by side as columns
    # future_stack=True keeps the NaN cells rather than silently dropping them, so all 7 frames fold to exactly the same set of rows and line up.
    table = pd.concat(
        {name: frame.stack(future_stack=True) for name, frame in group_a.items()},
        axis=1,
    )
    table.index.names = ["signal_date", "ticker"]
    table = table.reset_index()

    # Attach the 4 regime columns and the fill date by matching on the signal date, which repeats each value across that week's sectors
    regime = group_b_features(weekly, fred_daily)
    regime["fill_date"] = fill_dates(weekly.index, daily.index)
    table = table.merge(regime, left_on="signal_date", right_index=True, how="left")

    # Keep only the pairs where that sector actually had a closing price that week
    # Testing for "every feature is NaN" would not work here: the 4 regime columns go back to 1998 for every sector, so a row for XLC in 2005 would carry a curve slope and a credit spread and survive despite the sector not existing yet.
    had_price = weekly[SECTORS].stack(future_stack=True).notna()
    had_price.index.names = ["signal_date", "ticker"]
    keys = pd.MultiIndex.from_frame(table[["signal_date", "ticker"]])
    table = table[had_price.reindex(keys).to_numpy()]

    # Store the two date columns as YYYY-MM-DD text, matching how the prices table already stores dates
    # fill_date stays empty for the newest week, whose fill day has not been recorded yet.
    table["signal_date"] = table["signal_date"].dt.strftime("%Y-%m-%d")
    table["fill_date"] = table["fill_date"].dt.strftime("%Y-%m-%d")

    ordered = ["signal_date", "ticker", "fill_date", *FEATURE_COLUMNS]
    return table[ordered].sort_values(["signal_date", "ticker"]).reset_index(drop=True)


def write_feature_table(table: pd.DataFrame) -> int:
    """
    Drops the features table, recreates it, and inserts every row of the given frame.
    Returns the number of rows written; raises sqlite3.IntegrityError if the frame holds two rows with the same signal date and ticker.
    `to_sql(..., if_exists="append")` writes into the table that was just created rather than letting pandas invent its own schema without a primary key.
    """

    # Drop the table and build it again from scratch
    # A full rebuild rather than an append, for the same reason prices are re-pulled in full: Tiingo restates past adjusted prices when a dividend is paid, so appending would mix rows computed before a restatement with rows computed after it.
    conn = get_conn()
    conn.execute("DROP TABLE IF EXISTS features")
    feature_columns_sql = ",\n            ".join(f"{name} REAL" for name in FEATURE_COLUMNS)
    conn.execute(f"""
        CREATE TABLE features (
            signal_date TEXT NOT NULL,
            ticker      TEXT NOT NULL,
            fill_date   TEXT,
            {feature_columns_sql},
            PRIMARY KEY (signal_date, ticker)
        )
    """)

    # Insert every row, then commit and close
    # The primary key above makes a duplicate signal_date and ticker pair impossible rather than something to check for afterward.
    table.to_sql("features", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    return len(table)
