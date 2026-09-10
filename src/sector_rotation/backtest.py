import pandas as pd

from sector_rotation.config import SECTORS
from sector_rotation.db import get_conn
from sector_rotation.features import FEATURE_COLUMNS

# How many sectors the portfolio holds, equally weighted.
DEFAULT_TOP_N: int = 3

# What a single side of a trade costs, in basis points of the value traded.
# 5 is deliberately conservative. Interactive Brokers' explicit fees for this strategy come to roughly 0.66 per side plus a 0.21 SEC fee on sells, but the bid-ask spread and whatever the opening auction prints away from the mid are not in any fee schedule and are the larger unknown. See the decisions log.
DEFAULT_COST_BPS: float = 5.0


def load_returns() -> pd.DataFrame:
    """
    Reads the labels table and returns every ticker's absolute return over the week it was held, SPY included.
    Returns a DataFrame of weeks by 12 tickers; a week and sector with no label is NaN.
    `pivot` turns the long table, which has one row per week-and-sector pair, into the wide shape where each ticker gets its own column.
    """

    # Open the database connection, read the labels table into a long dataframe with real dates, close the connection
    conn = get_conn()
    long = pd.read_sql(
        "SELECT signal_date, ticker, excess_return, spy_return FROM labels ORDER BY signal_date, ticker",
        conn,
        parse_dates=["signal_date"],
    )
    conn.close()

    # Add SPY's return back onto each sector's excess return to recover the sector's own absolute return
    # The labels table stores the excess deliberately, since that is what the model predicts. The backtest needs absolute returns to compute what the portfolio actually earned.
    long["absolute_return"] = long["excess_return"] + long["spy_return"]

    # Reshape from one row per week-and-sector into one row per week with a column per sector
    wide = long.pivot(index="signal_date", columns="ticker", values="absolute_return")

    # Add SPY as its own column, taking the one spy_return value each week carries
    # Every sector in a week stores the same spy_return, so taking the first is the same as taking any of them.
    wide["SPY"] = long.groupby("signal_date")["spy_return"].first()

    return wide


def run_strategy(weights: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """
    Turns a week-by-week set of target weights into what the portfolio earned each week and how much of it had to be traded.
    Returns a DataFrame indexed by week with 3 columns: gross_return, turnover (the one-way fraction of the portfolio traded) and traded (both sides added together, which is what the cost is charged on).
    `div(series, axis=0)` divides every column of the frame by that series row by row, which is how the drifted weights get renormalised.
    """

    # Line the two frames up on the same weeks and tickers, treating a ticker with no weight that week as a weight of 0
    w = weights.reindex(columns=returns.columns).fillna(0.0)
    r = returns.reindex(index=w.index)

    # Replace the return with 0 wherever the weight is 0
    # 0 times NaN is NaN in pandas, not 0, so a sector that was not held but has no return would otherwise turn the whole week's return into NaN. A NaN return on a sector that *was* held is left alone, so it shows up rather than being hidden.
    r = r.where(w != 0, 0.0)

    # Multiply each week's weights by that week's returns and add them up
    # skipna=False so a held position with no return makes the whole week NaN. The default skips NaN, which would report a return of 0.0 for a week whose return is actually unknown, with nothing visible to say so.
    gross_return = (w * r).sum(axis=1, skipna=False)

    # Grow each position by its own return, then rescale the week's positions back to summing to 1
    # This is where the week ends up before any trading: a sector that outran the others is now above its target weight, and the drifted vector is what next week's target has to be compared against.
    grown = w * (1 + r)
    total = grown.sum(axis=1, skipna=False)
    drifted = grown.div(total.where(total != 0), axis=0)

    # Zero the weights only in a week that genuinely held nothing, leaving a week with an unknown return as NaN
    # Filling every empty cell instead would turn a held position with no return into a weight of 0, and next week would then read it as a fresh entry and report turnover that never happened.
    drifted = drifted.where(total != 0, 0.0)

    # Compare this week's target weights against last week's drifted weights, and split the differences into what was bought and what was sold
    # The first week has no prior position, so it compares against 0: everything is a buy and nothing is a sell. That is a real entry cost, which is why the buy-and-hold check is zero turnover *after* the first week.
    # fill_value fills only the row that shifting vacates, unlike fillna, which would also swallow a NaN left by a week whose return was unknown and turn it into a false fresh entry.
    previous = drifted.shift(1, fill_value=0.0)
    change = w - previous
    # skipna=False on both, for the same reason as the sums above: not knowing where a position started means not knowing how much of it was traded, and 0.0 is a specific wrong answer rather than an unknown one.
    bought = change.clip(lower=0).sum(axis=1, skipna=False)
    sold = (-change.clip(upper=0)).sum(axis=1, skipna=False)

    # Take the larger of the two as the one-way turnover, and their sum as the amount the cost is charged on
    # Halving the sum instead would be wrong in the first week, where you buy the whole portfolio and sell none of it: buys 1.0 and sells 0.0 halve to 0.5, but the portfolio really did turn over once. Taking the larger gives 1.0 there and matches the halved sum in every week where buys and sells balance.
    return pd.DataFrame(
        {
            "gross_return": gross_return,
            "turnover": pd.concat([bought, sold], axis=1).max(axis=1),
            "traded": bought + sold,
        }
    )


def apply_costs(result: pd.DataFrame, cost_bps: float = DEFAULT_COST_BPS) -> pd.DataFrame:
    """
    Charges a per-side trading cost against a strategy's gross returns and adds the cost and the net return as columns.
    Returns a copy of `result` with 2 extra columns, cost and net_return; the input is left untouched.
    `copy()` is what keeps the input unchanged, so the same run can be priced at several cost levels without the first call altering it.
    """

    # Multiply the amount traded by the per-side rate, converting basis points to a fraction
    # `traded` already counts both sides, so multiplying by the per-side rate charges each side once. A week that buys 10% and sells 10% has traded 0.20, and at 5 basis points that costs 0.20 x 0.0005.
    priced = result.copy()
    priced["cost"] = priced["traded"] * (cost_bps / 10_000)

    # Subtract the cost from what the portfolio earned that week
    # The cost lands in the week the trade happened, which is the week the position was entered rather than the week it was closed.
    priced["net_return"] = priced["gross_return"] - priced["cost"]

    return priced


def load_feature(name: str) -> pd.DataFrame:
    """
    Reads one column out of the features table and returns it with weeks down the side and sectors across the top.
    Returns a DataFrame of weeks by the 11 sectors; raises ValueError if `name` is not one of the stored feature columns.
    `pivot` turns the long table, which has one row per week-and-sector pair, into the wide shape where each sector gets its own column.
    """

    # Reject any column name that is not a real feature column
    # The name is pasted into the SQL string below, because SQL will not accept a placeholder in place of a column name. Checking it against the fixed list is what keeps that safe.
    if name not in FEATURE_COLUMNS:
        raise ValueError(f"name must be one of {FEATURE_COLUMNS}, got {name!r}")

    # Open the database connection, read the one column into a long dataframe with real dates, close the connection
    conn = get_conn()
    long = pd.read_sql(
        f"SELECT signal_date, ticker, {name} AS value FROM features ORDER BY signal_date, ticker",
        conn,
        parse_dates=["signal_date"],
    )
    conn.close()

    return long.pivot(index="signal_date", columns="ticker", values="value")


def equal_weights(selected: pd.DataFrame, columns: pd.Index) -> pd.DataFrame:
    """
    Turns a true-or-false frame of which sectors are held each week into target weights that spread the portfolio evenly across them.
    Returns a DataFrame of weeks by `columns`, each row summing to 1, or to 0 in a week where nothing was selected.
    `div(series, axis=0)` divides every column of the frame by that series row by row, which is how each week gets divided by its own count.
    """

    # Count how many sectors were selected each week and give each of them an equal share
    # A week with nothing selected would divide by 0, so those weeks are left at 0 rather than becoming infinity.
    count = selected.sum(axis=1)
    weights = selected.astype("float").div(count.where(count != 0), axis=0).fillna(0.0)

    # Widen to the full ticker list so every strategy hands run_strategy the same shape, with SPY present and empty
    return weights.reindex(columns=columns).fillna(0.0)


def spy_buy_and_hold(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the weights for holding SPY and nothing else, every week.
    Returns a DataFrame of weeks by every ticker in `returns`, with 1.0 in the SPY column and 0.0 everywhere else.
    """

    # Put the whole portfolio in SPY in every week
    weights = pd.DataFrame(0.0, index=returns.index, columns=returns.columns)
    weights["SPY"] = 1.0
    return weights


def equal_weight_sectors(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Builds the weights for holding every sector that traded that week, in equal proportion, rebalanced weekly.
    Returns a DataFrame of weeks by every ticker in `returns`, each row summing to 1 across the sectors valid that week.
    """

    # Select every sector that has a return that week, which is 9 before October 2015, then 10, then 11
    # Selecting on the return rather than on a fixed list of 11 is what keeps XLRE and XLC out before they listed, instead of holding a position in something that did not exist.
    selected = returns[SECTORS].notna()
    return equal_weights(selected, returns.columns)


def momentum_baseline(
    returns: pd.DataFrame,
    ranks: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> pd.DataFrame:
    """
    Builds the weights for holding the `top_n` sectors with the strongest 12-week relative momentum, in equal proportion.
    Returns a DataFrame of weeks by every ticker in `returns`, each row summing to 1 across the sectors picked that week, or to 0 in a week with no ranks.
    """

    # Select the sectors ranked 1 through top_n that also have a return that week
    # The second condition matters: a sector can carry a rank while its holding period has not closed, and holding it would turn the whole week's return into NaN.
    ranked = ranks.reindex(index=returns.index, columns=SECTORS)
    selected = (ranked <= top_n) & returns[SECTORS].notna()
    return equal_weights(selected, returns.columns)
