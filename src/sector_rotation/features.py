import pandas as pd
import sqlite3
from sector_rotation.config import SECTORS


def build_mom_features() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # Open a connection to your database file
    con = sqlite3.connect("../data/sector_rotation.db")

    # Build the "?" placeholders for the SQL query — one per ticker
    placeholders = ",".join("?" * len(SECTORS))

    q = f"SELECT date, ticker, value FROM prices WHERE ticker IN ({placeholders}) ORDER BY date, ticker"

    # Load into a df
    long = pd.read_sql(q, con, params=SECTORS, parse_dates=["date"])

    # Close the connection
    con.close()

    # reorganize the df so the data is the index, all the tickers are columns and the values are price values
    wide = long.pivot(index="date", columns="ticker", values="value")
    wide = wide[SECTORS]

    # resample the data so that we only have one piece of data per week instead of daily
    weekly = wide.resample("W-FRI").last()

    mom_4 = weekly.pct_change(4, fill_method=None)
    mom_12 = weekly.pct_change(12, fill_method=None)
    mom_26 = weekly.pct_change(26, fill_method=None)

    return mom_4, mom_12, mom_26