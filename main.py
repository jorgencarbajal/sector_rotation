import argparse

import pandas as pd

from sector_rotation.config import ALL_TICKERS, FRED_SERIES, START_DATE, TIINGO_TOKEN
from sector_rotation.backtest import (
    DEFAULT_COST_BPS,
    DEFAULT_TOP_N,
    apply_costs,
    equal_weight_sectors,
    load_feature,
    load_returns,
    momentum_baseline,
    run_strategy,
    spy_buy_and_hold,
    summarise,
    write_results,
)
from sector_rotation.db import init_db, table_exists
from sector_rotation.fetch import (
    export_hy_oas_csv,
    fetch_and_store_ticker,
    fetch_and_store_fred,
    load_hy_oas_csv,
)
from sector_rotation.features import (
    build_feature_table,
    fill_dates,
    load_daily_prices,
    to_weekly,
    write_feature_table,
)
from sector_rotation.labels import build_label_table, write_label_table


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


def build_dataset() -> None:
    """
    Rebuilds both modeling tables, features and labels, from whatever is currently in the prices table.
    Returns None; raises RuntimeError when the prices table holds no equity data, which means backfill has not been run.
    Named build_dataset rather than dataset only to keep the name distinct from the subcommand string it is registered under.
    """

    # Read the adjusted closes of the 12 Tiingo tickers out of prices and fold them into weekly bars
    print("Loading prices")
    daily = load_daily_prices()

    # If no equity rows came back, say so plainly instead of letting pandas raise a KeyError several steps later
    if daily.empty:
        raise RuntimeError("no price data found in the prices table - run backfill first")

    weekly = to_weekly(daily)
    print(f"  {len(daily)} daily rows, {len(weekly)} weekly rows")

    # Read the 3 FRED series, which are stored in the same table with the series id in the ticker column
    print("Loading FRED series")
    fred_daily = load_daily_prices(FRED_SERIES)

    # Build all 11 feature columns into one long table, then drop and rebuild the features table from it
    print("Building features")
    features = build_feature_table(weekly, daily, fred_daily)
    n = write_feature_table(features)
    print(f"  {n} rows written, {features['signal_date'].min()} to {features['signal_date'].max()}")

    # Read the adjusted opens, work out which day each week's trade fills on, and build the labels from those two
    # Opens rather than closes because that is what a fill is priced at, and the label has to measure a return the position could actually have earned.
    print("Building labels")
    opens = load_daily_prices(column="adj_open")
    labels = build_label_table(opens, fill_dates(weekly.index, daily.index))
    n = write_label_table(labels)
    print(f"  {n} rows written, {labels['signal_date'].min()} to {labels['signal_date'].max()}")


def run_backtest(cost_bps: float, top_n: int) -> None:
    """
    Runs every strategy that needs no model, writes the results folder, and prints the metrics table.
    Returns None; raises RuntimeError when the features or labels table is missing, which means dataset has not been run.
    """

    # Stop with a plain message if either modelling table is missing, rather than letting SQL raise about a table nobody mentioned
    for name in ("features", "labels"):
        if not table_exists(name):
            raise RuntimeError(f"no {name} table found - run dataset first")

    # Read every ticker's weekly return and the stored 12-week momentum rank
    print("Loading returns and ranks")
    returns = load_returns()
    ranks = load_feature("mom_rank_12w")
    print(f"  {len(returns)} weeks, {returns.index[0].date()} to {returns.index[-1].date()}")

    # Build the 3 lines that need no model, then charge each of them the same trading cost
    print(f"Running strategies at {cost_bps} bp per side, holding the top {top_n}")
    lines = {
        "SPY buy-and-hold": spy_buy_and_hold(returns),
        "equal weight": equal_weight_sectors(returns),
        "momentum baseline": momentum_baseline(returns, ranks, top_n),
    }
    priced = {name: apply_costs(run_strategy(weights, returns), cost_bps) for name, weights in lines.items()}

    # Write the 4 output files and print where they went
    print("Writing results")
    for path in write_results(priced):
        print(f"  {path}")

    # Print the metrics so a run says something without opening a file
    # Sharpe is the zero-rate figure and is labelled as such here, because quoting it plainly would overstate it - see the decisions log.
    metrics = pd.DataFrame({name: summarise(frame, priced["SPY buy-and-hold"]["net_return"]) for name, frame in priced.items()}).T
    print()
    print(metrics[["annual_return", "annual_volatility", "sharpe_rf_zero", "max_drawdown", "avg_turnover", "hit_rate"]].to_string(
        formatters={
            "annual_return": "{:+.2%}".format,
            "annual_volatility": "{:.2%}".format,
            "sharpe_rf_zero": "{:.3f}".format,
            "max_drawdown": "{:.1%}".format,
            "avg_turnover": "{:.2%}".format,
            "hit_rate": "{:.1%}".format,
        }
    ))
    print("\nSharpe assumes a risk-free rate of zero and is only valid for ranking these lines against each other.")


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
    subparsers.add_parser("dataset", help="drop and rebuild the features and labels tables from the prices table")
    backtest_parser = subparsers.add_parser("backtest", help="run every strategy that needs no model and write the results folder")
    backtest_parser.add_argument("--cost-bps", type=float, default=DEFAULT_COST_BPS, help="cost of one side of a trade, in basis points")
    backtest_parser.add_argument("--top-n", type=int, default=DEFAULT_TOP_N, help="how many sectors the portfolio holds")

    # Read the command line, look the command up in the table, and call it
    # Each entry is a small function of the parsed arguments, which is what lets backtest take options while the other 3 take none. Writing it as `commands[args.command]()` would mean giving every command an argument it ignores.
    args = parser.parse_args()
    commands = {
        "backfill": lambda a: backfill(),
        "update": lambda a: update(),
        "dataset": lambda a: build_dataset(),
        "backtest": lambda a: run_backtest(a.cost_bps, a.top_n),
    }
    commands[args.command](args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
