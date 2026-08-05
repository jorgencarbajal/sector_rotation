import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sector_rotation.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            date   TEXT NOT NULL,
            ticker TEXT NOT NULL,
            value  REAL NOT NULL,
            PRIMARY KEY (date, ticker)
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")


def read_prices(tickers, start=None):
    """
    Read long-format rows for the given tickers: (date, ticker, value).

    `tickers` is required, not optional: the prices table mixes sector ETFs and
    FRED macro series in the same `ticker` column, so reading everything and
    pivoting would produce a frame that is mostly NaN.

    Steps:
    1. Build one "?" placeholder per ticker -> "?,?,?". SQL has no native
       variable-length IN list, so the placeholder string has to be generated.
       The ticker values themselves still go through `params`, never into the
       query text - that is what keeps this injection-safe.
    2. Start the query and a `params` list. The order of `params` must match the
       order the "?" marks appear in the query; sqlite fills them positionally.
    3. If `start` was given, append a date floor and its matching param. Dates
       are stored as TEXT in ISO format (YYYY-MM-DD), which compares correctly
       with plain string >= , so no conversion is needed here.
    4. ORDER BY date, ticker so row order is deterministic run to run.
    5. Open a connection and hand the query to pandas. parse_dates=["date"]
       converts that TEXT column into real datetime64 values - required later,
       since .resample() only works on a datetime index.
    6. try/finally so the connection closes even if the read raises.
    """
    placeholders = ",".join("?" * len(tickers))
    q = f"SELECT date, ticker, value FROM prices WHERE ticker IN ({placeholders})"
    params = list(tickers)

    if start is not None:
        q += " AND date >= ?"
        params.append(start)

    q += " ORDER BY date, ticker"

    conn = get_conn()
    try:
        return pd.read_sql(q, conn, params=params, parse_dates=["date"])
    finally:
        conn.close()