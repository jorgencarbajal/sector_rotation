import requests
from sector_rotation.db import get_conn

def fetch_and_store(ticker, token, start="2005-01-01"):
    url = f"https://api.tiingo.com/tiingo/daily/{ticker}/prices"
    r = requests.get(url, params={"startDate": start, "token": token})
    r.raise_for_status()
    bars = r.json()

    rows = [(bar["date"][:10], ticker, bar["adjClose"]) for bar in bars]

    conn = get_conn()
    conn.executemany(
        "INSERT OR REPLACE INTO prices (date, ticker, value) VALUES (?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)