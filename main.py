import os
from sector_rotation.config import (
    SECTORS, START_DATE, TIINGO_TOKEN, FRED_TOKEN
)
from sector_rotation.fetch import fetch_and_store_ticker, fetch_and_store_fred
from sector_rotation.db import init_db


def pull_sectors(token: str) -> None:
    for ticker in SECTORS:
        n = fetch_and_store_ticker(ticker, token, START_DATE)
        print(f"{ticker}: {n} rows")


def pull_spy(token: str) -> None:
    n = fetch_and_store_ticker("SPY", token, START_DATE)
    print(f"SPY: {n} rows")


def pull_fred_data() -> None:
    for sid in ["DGS10", "DGS2", "BAMLH0A0HYM2"]:
        fetch_and_store_fred(sid)
        print(f"stored {sid}")


def main():
    # initialize the database
    # init_db()

    # pull_sectors(TIINGO_TOKEN)
    # pull_spy(TIINGO_TOKEN)
    pull_fred_data()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())