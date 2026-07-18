# Weekly ML Sector Rotation Model

## Goal
Beginner-friendly ML model that rotates among the 11 SPDR sector ETFs (XLK, XLE, XLF, XLV, XLI, XLP, XLY, XLB, XLRE, XLU, XLC) on a weekly cadence.

## User Background
- New to quant finance; completed a graduate data mining course
- Wants manageable scope, low learning curve, incremental complexity

## Model Spec
- Target: classification — will sector X beat SPY next week?
- Portfolio: hold top-3 ranked sectors, equal weight (no mean-variance optimization)
- Rebalance: signal from Friday close, execute Monday open, hold one week
- Model: gradient boosting (XGBoost/LightGBM) or random forest

### v1 features — Group A (sector-specific; vary across the 11 sectors each week)
- Momentum: 4/12/26-wk trailing return, each its own feature. Dividend/split-adjusted close.
- Relative momentum vs SPY: sector x-wk return minus SPY x-wk return.
- Cross-sectional momentum rank: rank the 11 sectors each week by trailing momentum (1 = best). Same signal as momentum, expressed as within-week position.
- Realized volatility: std of weekly returns, trailing 4/12-wk.
- Sector beta to SPY (rolling): slope of sector-on-SPY weekly-return regression over trailing N weeks. Interaction partner for regime features.

### v1 features — Group B (common/regime; identical across sectors within a week; useful only via interactions with Group A)
- Yield-curve slope (10Y−2Y or 10Y−3M) + weekly change.
- 10Y yield: weekly change only (level dropped, overlaps with slope).
- Credit spread: actual high-yield OAS (not HYG/LQD ratio). See Decisions Log for leakage handling.
- SPY trend state: above/below 40-wk MA, 0/1.

### v2 candidates (not yet)
- HMM regime switching, put/call ratio, ISM / macro releases (publication lag), fund-flow data, earnings-season dummies, news (Monday pre-bell, execute at open).
- Cut from v1: short-term reversal, correlation to SPY, distance from 52-wk high, relative volume, drawdown depth, VIX, cross-sectional dispersion, DXY/oil.

## Ground Rules
- Walk-forward validation ONLY — never random train/test splits
- Include transaction costs (~5-10 bps/trade)
- Benchmarks: buy-and-hold SPY and equal-weight sectors
- Weekly performance measurement
- Underperformance vs benchmark is a valid finding, not failure

## Working Style
- Challenge my reasoning when wrong; I'll do the same
- Concise responses; no files unless requested
- Flag error-prone steps and show your work there (data leakage, date alignment, cost math)
- When we lock a new decision in chat, remind me to add it to the Decisions Log

## Project Structure
- src-layout package (src/sector_rotation/), uv-managed, .env for Tiingo + FRED tokens
- Modules: config.py, db.py, fetch.py; main.py as runner; notebooks/ for prototyping

## Data Status
- All 11 sectors + SPY backfilled into `prices` table (Tiingo EOD, adjClose, daily bars)
- 3 FRED macro series loaded into same `prices` table (long format, series_id as ticker):
  - DGS10 — 16,119 rows, 1962-01-02 → current
  - DGS2 — 12,527 rows, 1976-06-01 → current
  - BAMLH0A0HYM2 (HY OAS) — 7,715 rows, 1996-12-31 → current. Verified continuous (0 gaps > 4 days, 0 duplicates)
- All raw source data acquired. Next: weekly resample + feature engineering.

## Decisions Log
- Storage: SQLite, single `prices` table, long format (date, ticker, value), (date, ticker) primary key, INSERT OR REPLACE for idempotent writes
- Provider (equities): Tiingo EOD endpoint, store `adjClose` (split/dividend-adjusted, CRSP method)
- Provider (macro): FRED series/observations endpoint (JSON). Separate fetch function from Tiingo — different API shape. Store raw levels as-is (no adjClose, no price-adjustment). FRED missing days marked "." — skip those rows on parse (don't store)
- Backfill: from inception (START_DATE = 1998-01-01; Tiingo clamps each ticker to its real start). FRED returns full history per series (predates 1998, fine). Store full history, choose train/test window at model time
- Bars: store daily, resample to weekly (Friday close) in pandas — not server-side
- Rebalance: signal from Friday close, execute Monday open, hold one week
- Credit spread: use actual high-yield OAS (FRED BAMLH0A0HYM2), not HYG/LQD ratio. Lag one business day (series publishes prior day's value next morning; Friday-close signal can only use Thursday's OAS). On weekly resample, align to last OAS on-or-before the lagged date; no blind forward-fill across gaps. [OPEN: confirm HY vs IG series]
- BAMLH0A0HYM2 API truncation: FRED API returns only the trailing ~3 years for this series (root cause unresolved — likely ICE BofA licensing or a realtime/vintage default; not fixed). Full 1996→present history was backfilled from a static CSV snapshot (GitHub source), verified against a separate DB snapshot: 6,322 overlap rows, 0 mismatches. The two sources stitched with no gap.
- BAMLH0A0HYM2 history depends on the CSV backfill, NOT the FRED fetch. Weekly re-runs only refresh the trailing 3yr via INSERT OR REPLACE (harmless — appends new dates, leaves old backfill untouched). BUT a rebuild-from-scratch would truncate OAS to 3yr. Keep BAMLH0A0HYM2.csv as a source file; any fresh DB build must reload it. [OPEN: fix fetch so function is correct standalone, or bake CSV load into rebuild path]
- Feature set v1: locked to Groups A and B above; other candidates cut or deferred to v2
- Momentum features (4/12/26-wk): resample daily→weekly first (W-FRI, .last()), THEN pct_change(n, fill_method=None). Order matters — resample-before-pct_change makes n mean weeks not days. fill_method=None prevents forward-fill fabricating 0% returns across the XLRE/XLC ragged start; early rows stay NaN, no fill. Computed on adjClose. Verified: XLC first-valid at 4/12/26wk = 2018-07-20 / 2018-09-14 / 2018-12-21.
- Partial final bar: weekly resample labels the current incomplete week with its Friday date but uses the last available daily close (e.g. a Wed close). Excluded from signals. [OPEN: implement drop rule — differs for live (run after real Friday close) vs backtest (drop trailing incomplete week)].