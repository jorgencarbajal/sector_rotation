import os
from pathlib import Path

import pandas as pd
import requests

from sector_rotation.db import get_conn
from sector_rotation.config import FRED_TOKEN

FRED_URL: str = "https://api.stlouisfed.org/fred/series/observations"

# One row of the prices table: date, ticker, value, adj_open. The 4th item is float | None because FRED rows carry no opening price and write None, which SQLite stores as NULL.
PriceRow = tuple[str, str, float, float | None]

# Built from __file__ rather than written as "../data/..." so the function works no matter which directory you run it from.
HY_OAS_SERIES: str = "BAMLH0A0HYM2"
HY_OAS_CSV_PATH: Path = Path(__file__).resolve().parent.parent.parent / "data" / f"{HY_OAS_SERIES}.csv"

# The true first observation of the series. An export that does not start here is coming from a database that lost the CSV backfill.
HY_OAS_FIRST_DATE: str = "1996-12-31"


def store_rows(rows: list[PriceRow]) -> None:
    """
    Writes a list of (date, ticker, value, adj_open) tuples into the prices table, replacing any row that already has the same date and ticker.
    Returns None; raises sqlite3.ProgrammingError with "Incorrect number of bindings" if a tuple does not have exactly 4 items.
    `executemany` runs the one statement once per tuple in the list, which is far faster than calling execute in a Python loop.
    """

    # INSERT OR REPLACE does not edit a row in place - it deletes the matching row and inserts a new one built only from the columns named here, so any column left out of this statement comes back as NULL.
    # That is why every tuple must carry all 4 values: a 3-column version of this statement would wipe adj_open off every equity row on each re-pull.
    conn = get_conn()
    conn.executemany(
        "INSERT OR REPLACE INTO prices (date, ticker, value, adj_open) VALUES (?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def load_hy_oas_csv() -> int:
    """
    Reads the committed high-yield OAS snapshot from data/BAMLH0A0HYM2.csv and writes its rows into the prices table.
    Returns the number of rows written; raises FileNotFoundError if the file is gone and KeyError if either column has been renamed.
    `dropna(subset=[...])` drops rows where that one column is empty, and `zip(dates, values)` walks two columns side by side, handing back one pair per row.
    """

    # The FRED API returns only the trailing 3 years of this series, so this file is the only source for 1996-12-31 through 2025-11-03. Deleting it loses 29 years of history that cannot be re-fetched.
    df = pd.read_csv(HY_OAS_CSV_PATH)

    # This CSV marks market holidays with an empty cell, unlike the API which marks them with a "." - 92 of its 7,622 rows are blank.
    # pandas reads an empty cell as NaN, and NaN is a float, so it would pass any check asking "is this a number" and land in SQLite as a NaN, which is neither NULL nor a usable value. dropna is what stops that.
    df = df.dropna(subset=[HY_OAS_SERIES])

    # The 4th value is None for the same reason as the API rows: a credit spread has no opening price.
    rows = [
        (date, HY_OAS_SERIES, float(value), None)
        for date, value in zip(df["observation_date"], df[HY_OAS_SERIES])
    ]

    store_rows(rows)
    return len(rows)


def export_hy_oas_csv() -> int:
    """
    Writes every BAMLH0A0HYM2 row in the prices table back out to data/BAMLH0A0HYM2.csv, so the committed snapshot never falls behind the database.
    Returns the number of rows written, or raises RuntimeError and writes nothing when the export would start after 1996-12-31 or would hold fewer rows than the file already does.
    `os.replace(temp, real)` swaps one file for another in a single step the operating system will not leave half-finished.
    """

    # Open data base connection, read sql into a dataframe, close the conneciton
    conn = get_conn()
    df = pd.read_sql(
        "SELECT date, value FROM prices WHERE ticker = ? ORDER BY date",
        conn,
        params=(HY_OAS_SERIES,),
    )
    conn.close()

    # If the df is empty or the first date does not equal true first date, throw error
    if df.empty or df["date"].iloc[0] != HY_OAS_FIRST_DATE:
        first = df["date"].iloc[0] if not df.empty else "nothing"
        raise RuntimeError(f"refusing to export {HY_OAS_SERIES}: series starts at {first}, expected {HY_OAS_FIRST_DATE}")

    # If the CSV already exists, read it, drop its blank rows, and throw an error if the dataframe has fewer rows than that file
    # This catches a database that still starts in 1996 but has had rows deleted out of the middle, which the date check above cannot see.
    if HY_OAS_CSV_PATH.exists():
        existing = pd.read_csv(HY_OAS_CSV_PATH).dropna(subset=[HY_OAS_SERIES])
        if len(df) < len(existing):
            raise RuntimeError(f"refusing to export {HY_OAS_SERIES}: {len(df)} rows would replace a file holding {len(existing)}")

    # Rename the two dataframe columns from date and value to observation_date and the series id
    # Those are the names the file has always used and the names load_hy_oas_csv reads it by.
    df.columns = ["observation_date", HY_OAS_SERIES]

    # Build a temp path next to the real file, write the dataframe to it, then rename it over the real file
    # A crash partway through the write damages only the temp file and leaves the CSV untouched.
    temp_path = HY_OAS_CSV_PATH.with_name(HY_OAS_CSV_PATH.name + ".tmp")
    df.to_csv(temp_path, index=False)
    os.replace(temp_path, HY_OAS_CSV_PATH)

    return len(df)


def fetch_and_store_fred(series_id: str) -> None:
    """
    This function takes the series id (in this case the choices are "DGS10", "DGS2", "BAMLH0A0HYM2") uses the api key to make an http request. It then loops through the returned response and appends the information into a list to store into the db.
    """
    params = {
        "series_id": series_id,
        "api_key": FRED_TOKEN,
        "file_type": "json",
    }
    r = requests.get(FRED_URL, params=params, timeout=30)
    r.raise_for_status()
    observations = r.json()["observations"]

    rows: list[PriceRow] = []

    for obs in observations:
        value = obs["value"]
        if value == ".":
            continue
        # The 4th value is None, which SQLite stores as NULL: a yield or a credit spread has no opening price, and a 0 here would be a number that later arithmetic would silently use.
        rows.append((obs["date"], series_id, float(value), None))

    store_rows(rows)


def fetch_and_store_ticker(ticker: str, token: str, start: str) -> int:
    """
    Fetches one ticker's full daily history from Tiingo starting at `start` and writes the adjusted close and adjusted open into the prices table.
    Returns the number of rows written; raises requests.HTTPError on a bad response and KeyError if a bar is missing adjOpen or adjClose.
    The list comprehension `[(...) for bar in bars]` builds the whole list of row tuples in one pass over the API response.
    """

    # Tiingo restates every adjusted price in a ticker's history whenever that ticker pays a dividend, so this always pulls from `start` rather than from the newest stored date - an incremental pull would leave old rows on the old adjustment factor and new rows on the new one, putting a fake jump at the seam.
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    r = requests.get(url, params={"startDate": start, "token": token})
    r.raise_for_status()
    bars = r.json()

    # bar["date"] arrives as a full timestamp like "2026-07-17T00:00:00.000Z", and [:10] slices off the first 10 characters to leave "2026-07-17".
    # Indexing with bar["adjOpen"] rather than bar.get("adjOpen") is deliberate: a missing field raises KeyError here, where .get would store a NULL open that only surfaces much later as a gap in the labels.
    rows = [(bar["date"][:10], ticker, bar["adjClose"], bar["adjOpen"]) for bar in bars]

    store_rows(rows)
    return len(rows)