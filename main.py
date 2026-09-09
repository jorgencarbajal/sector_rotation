import argparse

from sector_rotation.config import ALL_TICKERS, FRED_SERIES, START_DATE, TIINGO_TOKEN
from sector_rotation.db import init_db
from sector_rotation.fetch import (
    export_hy_oas_csv,
    fetch_and_store_ticker,
    fetch_and_store_fred,
    load_hy_oas_csv,
)


def pull_tickers() -> None:
    """
    Pulls the full daily history of all 12 Tiingo tickers and writes each one into the prices table.
    Returns None; raises requests.HTTPError on a bad response, which stops the run at the ticker that failed.
    Nothing is caught here on purpose: an exception leaving this function exits the program non-zero, which is how a scheduled run reports that it failed.
    """

    # For each of the 12 tickers, fetch its whole history from START_DATE and print how many rows were written
    for ticker in ALL_TICKERS:
        n = fetch_and_store_ticker(ticker, TIINGO_TOKEN, START_DATE)
        print(f"  {ticker}: {n} rows")


def pull_fred() -> None:
    """
    Pulls all 3 FRED macro series and writes them into the prices table.
    Returns None; raises requests.HTTPError on a bad response, which stops the run at the series that failed.
    """

    # For each of the 3 series, fetch its observations and print the series id once it is stored
    for series_id in FRED_SERIES:
        fetch_and_store_fred(series_id)
        print(f"  {series_id}: stored")


def backfill() -> None:
    """
    Builds the database from nothing: creates the schema, loads the committed CSV, pulls both APIs, then writes the CSV back out.
    Returns None; raises RuntimeError from the export step if the finished database would shorten the CSV instead of extending it.
    """

    print("Creating schema")
    init_db()

    print("Loading the high-yield spread CSV")
    n = load_hy_oas_csv()
    print(f"  {n} rows")

    print("Pulling Tiingo")
    pull_tickers()
    print("Pulling FRED")
    pull_fred()

    print("Exporting the high-yield spread CSV")
    n = export_hy_oas_csv()
    print(f"  {n} rows")


def update() -> None:
    """
    Refreshes an existing database: pulls both APIs in full, then writes the high-yield spread back out to the CSV.
    Returns None; raises RuntimeError from the export step if the database no longer holds the full spread history.
    """

    # Create the prices table if it is missing, and add the adj_open column if an older database lacks it
    print("Checking schema")
    init_db()

    # Pull the 12 Tiingo tickers, then the 3 FRED series
    # Both pull complete history rather than only new dates, because Tiingo restates every past adjusted price whenever a ticker pays a dividend.
    print("Pulling Tiingo")
    pull_tickers()
    print("Pulling FRED")
    pull_fred()

    # Write the high-yield spread back out to the CSV so the committed file never falls behind the database
    print("Exporting the high-yield spread CSV")
    n = export_hy_oas_csv()
    print(f"  {n} rows")


def main() -> int:
    """
    Reads the subcommand off the command line and runs it.
    Returns 0 when the command finishes, and exits non-zero by letting any exception propagate rather than catching it.
    `add_subparsers(dest="command", required=True)` makes argparse reject a run with no subcommand and print the list of valid ones.
    """

    # Build the argument parser and register one subcommand per function
    parser = argparse.ArgumentParser(description="Weekly sector rotation model")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("backfill", help="build the database from nothing: schema, CSV, both APIs")
    subparsers.add_parser("update", help="refresh an existing database from both APIs")

    # Read the command line, look the command up in the table, and call it
    args = parser.parse_args()
    commands = {"backfill": backfill, "update": update}
    commands[args.command]()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
