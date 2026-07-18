import requests
from sector_rotation.db import get_conn
from sector_rotation.config import FRED_TOKEN

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


def store_rows(rows):
    conn = get_conn()
    conn.executemany(
        "INSERT OR REPLACE INTO prices (date, ticker, value) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()


def fetch_and_store_fred(series_id):
    params = {
        "series_id": series_id,
        "api_key": FRED_TOKEN,
        "file_type": "json",
    }
    r = requests.get(FRED_URL, params=params, timeout=30)
    r.raise_for_status()
    observations = r.json()["observations"]

    rows = []

    for obs in observations:
        value = obs["value"]
        if value == ".":
            continue
        rows.append((obs["date"], series_id, float(value)))

    store_rows(rows)


def fetch_and_store_ticker(ticker, token, start):
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    r = requests.get(url, params={"startDate": start, "token": token})
    r.raise_for_status()
    bars = r.json()

    rows = [(bar["date"][:10], ticker, bar["adjClose"]) for bar in bars]

    store_rows(rows)
    return len(rows)