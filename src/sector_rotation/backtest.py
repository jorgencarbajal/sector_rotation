from pathlib import Path

import pandas as pd

from sector_rotation.config import SECTORS
from sector_rotation.db import get_conn, table_exists
from sector_rotation.features import FEATURE_COLUMNS

# How many sectors the portfolio holds, equally weighted.
DEFAULT_TOP_N: int = 6

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


def top_n_by_score(
    returns: pd.DataFrame,
    scores: pd.DataFrame,
    top_n: int = DEFAULT_TOP_N,
) -> pd.DataFrame:
    """
    Builds the weights for holding the `top_n` sectors with the highest score that week, in equal proportion.
    Returns a DataFrame of weeks by every ticker in `returns`, each row summing to 1 across the sectors picked that week, or to 0 in a week with no scores.
    `rank(axis=1, ascending=False)` orders each week's sectors from highest score to lowest, so the top_n are the ones ranked at or below top_n.
    """

    # Blank the score of any sector that has no return that week, then order the rest by score and select the best top_n
    # Ranking here rather than reading a stored rank is what lets one function serve both callers: the momentum baseline hands it the 12-week momentum percentile, the model line hands it the predicted excess return.
    # The blanking happens before the ranking, not after. A sector can carry a score while its holding period has not closed, and holding it would turn the whole week's return into NaN. Filtering after ranking would drop it but leave its rank slot empty, so the line would hold top_n minus 1 rather than promoting the next sector.
    aligned = scores.reindex(index=returns.index, columns=SECTORS).where(returns[SECTORS].notna())
    ordered = aligned.rank(axis=1, ascending=False, method="first")
    selected = ordered <= top_n
    return equal_weights(selected, returns.columns)


def max_drawdown(net_return: pd.Series) -> float:
    """
    Finds the worst peak-to-trough fall the strategy ever suffered, as a negative fraction.
    Returns 0.0 for a series that never falls below a previous high, and NaN for an empty one.
    `cumprod` multiplies the running total forward week by week, and `cummax` carries the highest value seen so far down the series.
    """

    # Grow one dollar week by week, then compare each week against the highest the curve had reached by then
    curve = (1 + net_return).cumprod()
    drawdown = curve / curve.cummax() - 1

    # Take the deepest point, clipping a tiny positive rounding error back to a clean 0
    # A curve that only ever rises has a drawdown of exactly 0, but floating point division can leave it a hair above, and a positive maximum drawdown is a nonsense number to print.
    return float(min(drawdown.min(), 0.0)) if len(drawdown) else float("nan")


def summarise(priced: pd.Series | pd.DataFrame, benchmark: pd.Series | None = None) -> dict[str, float]:
    """
    Turns one strategy's weekly results into the summary figures the pass rule is judged on.
    Returns a dict of annual return, annual volatility, zero-rate Sharpe, max drawdown, average turnover and hit rate; volatility of 0 gives a Sharpe of NaN rather than dividing by zero.
    `sqrt(52)` scales a weekly standard deviation up to an annual one, because variance adds across independent weeks and standard deviation is its square root.
    """

    # Pull the weekly net return and turnover out, accepting either the full frame or just the return series
    net = priced["net_return"] if isinstance(priced, pd.DataFrame) else priced
    turnover = priced["turnover"] if isinstance(priced, pd.DataFrame) else None
    net = net.dropna()

    # Compound the weekly returns into a total, then find the steady yearly rate that would have produced it
    # The span runs from the first signal date to the last one plus 7 days, because the last week's return is earned over the week after its signal date. Measuring signal date to signal date counts one week fewer than the money was actually invested and overstates every line's annual return by about 0.01 of a point.
    years = ((net.index[-1] - net.index[0]).days + 7) / 365.25
    total_growth = float((1 + net).prod())
    annual_return = total_growth ** (1 / years) - 1

    # Scale the week-to-week standard deviation up to a yearly figure
    annual_volatility = float(net.std() * (52 ** 0.5))

    # Divide return by volatility, with the risk-free rate taken as zero
    # A perfectly flat series has no volatility and no meaningful Sharpe, so it returns NaN rather than dividing by zero. The zero rate is deliberate and only valid for ranking lines against each other - see the decisions log.
    sharpe = annual_return / annual_volatility if annual_volatility > 0 else float("nan")

    summary = {
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "sharpe_rf_zero": sharpe,
        "max_drawdown": max_drawdown(net),
        "total_growth": total_growth,
        "weeks": float(len(net)),
    }

    # Average how much of the portfolio was traded each week, skipping the first week's full entry
    # The entry is a one-off cost of starting, not part of how much the strategy trades week to week, and leaving it in would overstate a buy-and-hold line as trading 1/n of itself per week.
    if turnover is not None:
        summary["avg_turnover"] = float(turnover.iloc[1:].mean())

    # Count the fraction of weeks the strategy beat the benchmark it is measured against
    if benchmark is not None:
        aligned = benchmark.reindex(net.index)
        summary["hit_rate"] = float((net > aligned).mean())

    return summary


def returns_by_year(net_return: pd.Series) -> pd.Series:
    """
    Compounds the weekly returns whose signal date falls in each year.
    Returns a Series indexed by year holding that year's total return; a partial year at either end is compounded from whatever weeks it has.
    `groupby(index.year)` splits the weeks into years by their signal date, which is what makes each year's figure stand on its own.
    """

    # Multiply the weeks whose signal date falls in each year together and subtract 1
    # A single annual return hides whether a strategy won steadily or won once, which is the whole reason for listing years separately.
    # These years are labelled by signal Friday, not by the dates the money actually moved: a week signalled on the last Friday of December is held into January and still counts as December's year. That shifts each figure by about a week against a published calendar-year return - checked against the S&P 500 total return, the shift moves individual years by up to 6 points while the 27-year compound stays within 0.07. It does not affect the pass rule, which compares lines bucketed identically. Do not quote a single year from here against an outside source; compute it from adjusted closes instead.
    net = net_return.dropna()
    return (1 + net).groupby(net.index.year).prod() - 1


# Where every backtest run writes its output. Git-ignored, and overwritten rather than added to on each run.
RESULTS_DIR: Path = Path(__file__).resolve().parent.parent.parent / "results"

# One fixed colour per line, so a line keeps its colour whatever else is on the chart.
# Assigning by position instead would repaint the other 3 the moment the model line joins them. The 4 hues are slots 1 to 4 of a palette validated for colourblind separation: worst adjacent pair 9.1 on the protan check against a target of 8.
LINE_COLOURS: dict[str, str] = {
    "SPY buy-and-hold": "#2a78d6",
    "equal weight": "#eb6834",
    "momentum baseline": "#1baf7a",
    "model": "#eda100",
}

# Ink for text and for the grid. Labels never wear the series colour - the line arriving at the label is what carries its identity.
INK: str = "#0b0b0b"
INK_MUTED: str = "#52514e"
GRID: str = "#e3e2df"


def plot_comparison(priced: dict[str, pd.DataFrame], path: Path) -> None:
    """
    Draws one figure comparing the lines: what a dollar grew to on top, and how far each line sat below its own previous high underneath.
    Returns None, writing a PNG to `path`; a line whose name is absent from LINE_COLOURS raises KeyError rather than being given a made-up colour.
    `matplotlib.use("Agg")` picks the renderer that writes files without a screen, which is what lets this run over SSH on the server.
    """

    # Pick the renderer that needs no display, before importing pyplot
    # pyplot chooses a backend on import, and on a machine with no screen the default fails. Setting it first is what makes this work under a systemd timer.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Stack two panels sharing one date axis, giving the growth curves 3 times the height of the drawdowns
    # The right edge is left empty by the figure margin rather than by widening the date axis, which would draw years past the end of the data.
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True, height_ratios=[3, 1])
    figure.subplots_adjust(left=0.08, right=0.78, top=0.92, bottom=0.08, hspace=0.08)

    for name, frame in priced.items():
        net = frame["net_return"].fillna(0.0)
        curve = (1 + net).cumprod()
        drawdown = curve / curve.cummax() - 1

        # Draw the growth curve on a log scale and the drawdown below it
        # Log scale because equal percentage moves have to look equal: over 27 years on a linear axis the first decade is a flat line at the bottom and every pixel of movement belongs to the last few years.
        # Drawdowns are drawn as lines rather than filled areas, because 3 translucent fills stacked in the same band turn into mud and none of them stays readable.
        top.plot(curve.index, curve, color=LINE_COLOURS[name], linewidth=1.8, label=name)
        bottom.plot(drawdown.index, drawdown, color=LINE_COLOURS[name], linewidth=1.2)

        # Write the line's name and final value in the margin beyond where the line ends
        # Two of these 4 colours fall below 3 to 1 contrast on a white background, so a reader must not have to rely on colour alone to tell the lines apart. The label is in text ink; the line running into it carries the identity.
        top.annotate(
            f"  {name}  {curve.iloc[-1]:.1f}x",
            xy=(curve.index[-1], curve.iloc[-1]),
            va="center", fontsize=9, color=INK, annotation_clip=False,
        )

    # Label the log axis at the multiples a reader actually thinks in, rather than at powers of 10
    top.set_yscale("log")
    top.set_yticks([0.5, 1, 2, 5, 10])
    top.set_yticklabels(["0.5x", "1x", "2x", "5x", "10x"])
    top.minorticks_off()
    top.set_ylabel("one dollar grows to", color=INK_MUTED, fontsize=9)
    top.set_title("Sector rotation backtest, net of costs", color=INK, fontsize=12, loc="left")

    bottom.set_ylabel("below previous high", color=INK_MUTED, fontsize=9)
    bottom.set_yticks([0, -0.2, -0.4, -0.6])
    bottom.set_yticklabels(["0%", "-20%", "-40%", "-60%"])

    # Push the grid and the frame into the background so the data is what the eye lands on
    for axis in (top, bottom):
        axis.grid(True, color=GRID, linewidth=0.7)
        axis.set_axisbelow(True)
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(GRID)
        axis.tick_params(colors=INK_MUTED, labelsize=9)

    top.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK_MUTED)

    figure.savefig(path, dpi=150)
    plt.close(figure)


def write_results(priced: dict[str, pd.DataFrame], benchmark: str = "SPY buy-and-hold") -> list[Path]:
    """
    Writes every output of one backtest run into the results folder, overwriting whatever was there before.
    Returns the list of paths written: the weekly figures, the metrics table, the per-year returns and the comparison chart.
    `mkdir(parents=True, exist_ok=True)` creates the folder when it is missing and does nothing when it is already there.
    """

    # Create the results folder if this is the first run on this machine
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Write every week of every line side by side, with the line name as the outer column level
    weekly = pd.concat(priced, axis=1)
    weekly_path = RESULTS_DIR / "weekly_returns.csv"
    weekly.to_csv(weekly_path)

    # Summarise each line into one row, measuring hit rate against the benchmark line
    benchmark_net = priced[benchmark]["net_return"]
    metrics = pd.DataFrame({name: summarise(frame, benchmark_net) for name, frame in priced.items()}).T
    metrics_path = RESULTS_DIR / "metrics.csv"
    metrics.to_csv(metrics_path)

    # Break each line down into calendar years, since one annual figure cannot show whether a line won steadily or won once
    by_year = pd.DataFrame({name: returns_by_year(frame["net_return"]) for name, frame in priced.items()})
    by_year_path = RESULTS_DIR / "returns_by_year.csv"
    by_year.to_csv(by_year_path)

    chart_path = RESULTS_DIR / "comparison.png"
    plot_comparison(priced, chart_path)

    return [weekly_path, metrics_path, by_year_path, chart_path]


def load_predictions() -> pd.DataFrame:
    """
    Reads the predictions table and returns it with weeks down the side and sectors across the top.
    Returns a DataFrame of weeks by the sectors predicted, or an empty DataFrame when the table does not exist.
    `pivot` turns the long table, which has one row per week-and-sector pair, into the wide shape the weighting functions read.
    """

    # Return nothing rather than raising when no walk-forward run has happened yet, so the backtest can simply omit the model line
    if not table_exists("predictions"):
        return pd.DataFrame()

    # Open the database connection, read the predictions into a long dataframe with real dates, close the connection
    conn = get_conn()
    long = pd.read_sql(
        "SELECT signal_date, ticker, predicted_excess FROM predictions ORDER BY signal_date, ticker",
        conn,
        parse_dates=["signal_date"],
    )
    conn.close()

    return long.pivot(index="signal_date", columns="ticker", values="predicted_excess")
