# Weekly sector rotation model

A walk-forward machine learning model that ranks the 11 SPDR sector ETFs each week and holds the top few, tested against three benchmarks over 2005 to 2026.

**It does not work.** The finding is written up below. The code is complete and correct through the backtest; the live-trading and server stages were deliberately not built, because there is nothing worth running.

For how the project is organised, every decision and why it was made, see `CLAUDE.md`.

## What it does

Each Friday, eleven features are computed for every sector — three horizons of momentum relative to SPY, its standing among the other sectors, two measures of realised volatility, its beta to the market, and four features describing the wider regime (the yield-curve slope, that slope's weekly change, the high-yield credit spread, and whether SPY is above its 40-week average).

A random forest predicts each sector's return over the coming week relative to SPY. The three highest predictions are held equal weight, bought at Monday's open and sold at the next Monday's open.

The model is refitted every week on only the data that existed at the time, 1,132 times in total, so every prediction is genuinely out of sample.

## The result

Over 2004-12-24 to 2026-08-28, net of 5 basis points per side:

| line | annual return | volatility | Sharpe | max drawdown | weekly turnover |
|---|---|---|---|---|---|
| SPY buy-and-hold | **+10.89%** | 17.41% | **0.626** | -55.2% | 0.00% |
| equal weight, all 11 sectors | +10.32% | 17.06% | 0.605 | -52.9% | 0.63% |
| momentum baseline, top 3 | +6.54% | 17.05% | 0.383 | -49.7% | 21.66% |
| the model, top 3 | +6.05% | 19.31% | 0.314 | -66.0% | 40.37% |

Sharpe assumes a risk-free rate of zero and is only meaningful for ranking these four against each other.

The pass rule was written down before the backtest ran: the model had to beat the best of the other three on annual return, on Sharpe, and in more than half the calendar years. It failed all three, and failed them again when re-run at 0.75 basis points, the realistic cost floor for this broker. It is also the worst line on risk — the deepest drawdown, the highest volatility, and by far the most trading.

## Why it failed

**The signal was never there.** Before the model was built, the strongest single feature was measured directly: average weekly return relative to SPY, grouped by 12-week momentum rank across 13,870 sector-weeks. The best-ranked sector averaged -0.034% a week and the ninth averaged +0.096% — sloping the wrong way, and every win rate between 48% and 51%. Nothing significant in either direction.

**The regime bet lost too.** The four regime features existed to test a specific idea: that momentum pays inside particular market conditions even though it does not on average. Splitting the model's weekly performance by those conditions, it loses in every one — above and below the 40-week average, and in all three terciles of the credit spread.

**Acting on the model less always helped.** Holding more sectors improved both return and Sharpe at every step, from +5.27% holding one to +10.38% holding all eleven. Holding all eleven means the ranking is doing nothing, and that still trailed SPY. The ranking has negative value: the optimal amount to use is none.

**The regime features were worse than useless.** Rerunning the whole walk-forward on the seven sector-specific features alone, with the four regime features dropped, *improved* every measure: +6.85% against +6.05%, Sharpe 0.356 against 0.314, drawdown -62.8% against -66.0%. They gave the forest four more columns to find spurious structure in. That closes the thesis completely — the regime features existed to tell the model when to trust momentum, and the model was better off without them.

**The forest itself says the same thing.** Feature importances are nearly flat — nine of eleven features between 0.054 and 0.130, against 0.091 for an even split. It split on everything equally because nothing was more informative than anything else.

## What is worth keeping

The infrastructure is sound and the checks are what make the result trustworthy. Chaining 1,445 weekly returns reproduces the raw price ratio to 3.55e-15. The adjusted closes match published S&P 500 total returns to a mean absolute difference of 0.07 percentage points across 27 calendar years. Nine tests cover the four places where a mistake would be silent and profitable, each verified to fail when the thing it guards is broken.

Three real bugs were caught by those checks rather than by the results looking wrong:

- Trades were priced at the closing price rather than the opening price they would actually fill at.
- The closed-label rule was written one week too loose, which would have trained the model on the opening price it was about to trade into.
- Reading the FRED series walked back over missing dates but not over present dates holding no value, silently emptying the yield-curve slope in 29 weeks and costing 67 weeks of training data.

Any of the three would have made the backtest look better than the truth.

## Running it

The project uses uv and is pinned to Python 3.12. It needs a `.env` holding `TIINGO_TOKEN` and `FRED_TOKEN`.

```
uv sync                    # install dependencies
uv run pytest              # run the tests, under a second, no database needed

uv run main.py backfill    # build the database from nothing: schema, CSV, both APIs
uv run main.py update      # refresh an existing database from both APIs
uv run main.py dataset     # drop and rebuild the features and labels tables
uv run main.py backtest    # run the lines, write results/  (--cost-bps, --top-n)
```

The walk-forward run that produces the model's predictions is not yet a subcommand; it lives in `sector_rotation.model.walk_forward_predictions` and takes about 15 minutes.

`data/BAMLH0A0HYM2.csv` is committed and is the only source for the high-yield spread before 2023 — the FRED API returns only the trailing three years. A rebuild that skips it silently truncates 27 years of history to three.
