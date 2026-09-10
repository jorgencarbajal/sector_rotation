import pandas as pd

from sector_rotation.config import SECTORS
from sector_rotation.db import get_conn


def opens_at(opens: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    """
    Looks up every ticker's opening price on the given dates, one date per row of the input.
    Returns a DataFrame indexed the same way `dates` is, with one column per ticker; a row whose date is missing or NaT comes back all NaN.
    `reindex` pulls rows out by label rather than by position, so a date that is not in the frame yields NaN instead of raising.
    """

    # Relabel from fill dates to signal dates so the buy and sell frames share an index and can be divided
    looked_up = opens.reindex(dates.to_numpy())
    looked_up.index = dates.index
    return looked_up


def holding_period_returns(opens: pd.DataFrame, fill_dates: pd.Series) -> pd.DataFrame:
    """
    Computes every ticker's return from each week's fill open to the following week's fill open, which is the period a position is actually held for.
    Returns a DataFrame of weeks by every ticker in `opens`, SPY included; the newest week is all NaN because its holding period has not finished.
    `shift(-1)` moves every value up one row, so each week's row ends up holding the *following* week's fill date.
    """

    # Line up each week with the fill date that closes its holding period, which is the next week's fill date
    sell_dates = fill_dates.shift(-1)

    # Look up the opening prices on the buy date and on the sell date
    buy = opens_at(opens, fill_dates)
    sell = opens_at(opens, sell_dates)

    # Divide the selling price by the buying price and subtract 1, giving every ticker its return over the week actually held
    # These are opening prices on both ends because that is when trades fill. Measuring Friday close to Friday close would credit the weekend move between Friday's close and Monday's open, which the position does not own.
    return sell / buy - 1


def build_labels(opens: pd.DataFrame, fill_dates: pd.Series) -> pd.DataFrame:
    """
    Computes each sector's return over its holding period minus SPY's return over those same two dates.
    Returns a DataFrame of weeks by the 11 sectors; the newest week is all NaN because its holding period has not finished.
    `sub(series, axis=0)` subtracts one column from every column of the frame, matching them up row by row.
    """

    # Subtract SPY's return over the same two dates from every ticker's return
    # SPY's own column becomes exactly 0 here, since it is SPY minus SPY, which is worth checking as proof the dates lined up and is why SPY is dropped on the next line.
    returns = holding_period_returns(opens, fill_dates)
    excess = returns.sub(returns["SPY"], axis=0)

    # Keep the 11 sectors, dropping the all-zero SPY column
    # reindex rather than excess[SECTORS]: selecting raises when a sector is absent from the input, while reindex gives it an all-NaN column and lets the caller decide what a missing sector means. Same choice, for the same reason, as in load_daily_prices.
    return excess.reindex(columns=SECTORS)


def build_label_table(opens: pd.DataFrame, fill_dates: pd.Series) -> pd.DataFrame:
    """
    Turns the wide per-sector labels into a long table with one row per week and sector, ready to join against the features table.
    Returns a DataFrame of roughly 14,000 rows and 4 columns - signal_date, ticker, excess_return, spy_return - sorted by date then ticker.
    `stack(future_stack=True)` folds the sector columns down into rows, turning a weeks-by-sectors frame into one value per week-and-sector pair while keeping the NaN cells.
    """

    # Compute every ticker's return over the holding period, then split it into the per-sector excess and SPY's own return
    # Both come off the same frame so the two numbers cannot drift apart. A sector's absolute return is recovered later as excess_return + spy_return.
    returns = holding_period_returns(opens, fill_dates)
    excess = returns.sub(returns["SPY"], axis=0).reindex(columns=SECTORS)

    # Fold the sector columns down into rows
    table = excess.stack(future_stack=True).rename("excess_return")
    table.index.names = ["signal_date", "ticker"]
    table = table.reset_index()

    # Attach SPY's return for that week, which is the same number for every sector in the week
    table["spy_return"] = table["signal_date"].map(returns["SPY"])

    # Drop the rows with no label, which are weeks where the sector had not listed yet or the holding period has not closed
    # A row with no label teaches the model nothing, so leaving them out means joining this table against features hands you exactly the trainable set.
    # Dropping on excess_return alone also removes every row with no spy_return, because a missing SPY return makes the excess NaN too.
    table = table.dropna(subset=["excess_return"])

    # Store the date as YYYY-MM-DD text, matching how the prices and features tables already store dates
    table["signal_date"] = table["signal_date"].dt.strftime("%Y-%m-%d")

    return table.sort_values(["signal_date", "ticker"]).reset_index(drop=True)


def write_label_table(table: pd.DataFrame) -> int:
    """
    Drops the labels table, recreates it, and inserts every row of the given frame.
    Returns the number of rows written; raises sqlite3.IntegrityError if the frame holds two rows with the same signal date and ticker.
    `to_sql(..., if_exists="append")` writes into the table that was just created rather than letting pandas invent its own schema without a primary key.
    """

    # Drop the table and build it again from scratch
    # A full rebuild rather than an append, for the same reason prices are re-pulled in full: Tiingo restates past adjusted opens when a dividend is paid, so appending would mix labels computed before a restatement with labels computed after it.
    conn = get_conn()
    conn.execute("DROP TABLE IF EXISTS labels")
    conn.execute("""
        CREATE TABLE labels (
            signal_date   TEXT NOT NULL,
            ticker        TEXT NOT NULL,
            excess_return REAL NOT NULL,
            spy_return    REAL NOT NULL,
            PRIMARY KEY (signal_date, ticker)
        )
    """)

    # Insert every row, then commit and close
    # excess_return is NOT NULL here because the rows without one were already dropped, so a NULL arriving would mean something upstream changed.
    table.to_sql("labels", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    return len(table)
