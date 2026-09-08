# CLAUDE.md

Guidance for Claude Code when working in this repository.

# Working preferences

## How to write to me

Write in plain English. Assume I'm smart but not inside your head.

- Explain things in ordinary words first. If a term is genuinely necessary, define it the first time you use it.
- Don't invent labels, names, or shorthand for concepts. If a thing doesn't already have a name, describe it instead of naming it.
- Don't borrow jargon from other fields as a compliment or a shortcut — "first-class," "surface," "unlock," "orchestrate," "leverage." Use the ordinary word.
- No metaphors, no dramatic framing. A normal step is a normal step, not a "breakthrough" or a "gotcha."
- Don't write "not X, but Y," and don't argue against a position I never took. Say the thing you mean and stop.
- Say why something matters, not just what it is. "This clue used to be useless because X" is more useful than "this clue is now valid."
- Prefer full sentences over fragments and bullet soup. Bullets are fine for genuine lists; don't use them to avoid writing prose.
- Spell out numbers in context. "11 of 20" means nothing on its own — say 11 of what, out of which 20.
- No vague quantifiers. Not "most," "several," "generally," "at least some." Give a number. If you picked the number yourself, say so and say what it depends on.
- No filler openers ("Great question", "Absolutely"). Start with the answer.
- Keep responses short and digestible. A few lines, not a wall of text. I will ask when I want more detail, and leading with everything wastes both our time.

When you're unsure, or something in my request doesn't parse, say so directly and ask. Don't guess and move on. If you think I'm wrong, tell me — I'd rather be corrected than agreed with.

If I've just pasted something dense and asked you to explain it, rewrite it in your own words. Don't restate it with the same vocabulary rearranged.

## When you give me a list of items or next steps

This is where your writing goes ambiguous, so these are strict.

- Tell me what each item is asking of me. There are only a few kinds: a decision you already made and are reporting, a decision you need from me, a fact you want me to verify, or a task for me to do. Put that in the item's header — "Three defaults I picked, say if you disagree," "Decide before Phase 4," "Verify this before relying on it."
- Never mix those kinds inside one item without marking which is which. If I can't tell whether a sentence is a report or an instruction, the item is broken.
- Headers name the action, not the category. "Three decisions I made" — not "Open decisions to close."
- Lead with the criteria, the rule, or the answer. Motivation, background, and the reason a thing matters come after it, or get cut.
- One item, one topic. If a parameter choice isn't part of the criteria it sits next to, it gets its own item.
- Say who does what. "Check with the agent" is unclear. Say whether I'm asking the agent, or the agent asserts it at runtime, or I'm reading a doc.
- If ordering matters, put it in the order. Don't write "this is the one that matters most" inside item 2.
- Flag the parts you're least sure about, especially numbers you invented and external facts about how a service behaves. Say what breaks if you're wrong.

## When you explain a change to code

Show me the actual text, before and after. Describing an edit in prose is where you go ambiguous, and it costs a round trip every time.

- Quote the real line as it stands now, then the real line as it will be. Not a summary of what changes about it.
- Name the exact place the thing lives. "The SQL string inside `store_rows`" and "the tuples the caller builds" are two different places, and calling either one "a parameter" when the function has one parameter is the kind of slip that sends me down the wrong path.
- If I state the problem back to you and get a word wrong, correct that specific word first, before explaining anything else.
- Design discussion still comes first and still comes in prose. This rule starts once we are talking about a specific edit to a specific line.

## How we work

I write the code. Build one file, class, or function at a time, at my pace. Do not generate a skeleton, several modules, or speculative structure in one go, and do not create files I didn't ask for. Designing and discussing up front is welcome; wholesale implementation is not.

Present one step or one decision at a time, then stop and wait for my approval before continuing.

Explain the design before you write it. When I ask you to walk me through a design, I want the reasoning, the tradeoffs, and one clear recommendation — not a menu of options for me to pick from.

No code until I've said I understand the step and I'm ready for it.

Never spend money on my behalf. Paid API calls and anything else that costs something get asked about first.

## Code comments

I am new to Python, so comment generously.

Write inline comments as single unwrapped lines — one comment per physical line, however long it gets. Never hard-wrap one comment across several `#` lines. I collapse long lines with alt+Z in the editor, and hard-wrapped comments defeat that.

Every function gets a docstring of two to three sentences, no more:

1. What it does.
2. What it returns, including what it returns on failure — `None`, `[]`, or raises.
3. Name any Python or library syntax in it that a learner would not recognise — decorators, `async with`, `yield`, context managers, comprehensions, the walrus `:=`, dunder methods — and say in one clause what that syntax does.

Prefer naming the mechanism over describing the intent: "`async with` waits for the lock without blocking the event loop" beats "safely acquires the lock".

Anything about why the code is shaped this way — a site that broke it, a deploy trap, a measured result — goes in a `#` comment under the docstring, not in the docstring itself.

If a function does more than three distinct things, don't compress it into three sentences. Say that it's doing too much, then write it the longer way: a two-line docstring plus a one-line `#` comment on each block.

Inside the body, every block gets a comment that says plainly what those lines do, in the order they do it. Read the code and narrate it. That comment comes first; if there is also something to explain about why the block is shaped that way, it goes on a second `#` line under the first one.

These are the shape I want:

```python
# Open the database connection, read the query into a dataframe, close the connection
conn = get_conn()
df = pd.read_sql(...)
conn.close()

# If the dataframe is empty or the first date does not equal the true first date, throw an error
if df.empty or df["date"].iloc[0] != HY_OAS_FIRST_DATE:
    raise RuntimeError(...)
```

Note what those do: they name the actual operations — open, read, close; empty, first date, throw — in sequence. Don't label a block with a role it plays elsewhere ("Guard 2 catches a database that..."), don't lead with the rationale, and don't assume I remember what a name meant three blocks ago. The rationale is welcome, on its own line underneath.

## Terminal

In my git bash, Claude Code's `!` prefix silently drops everything after `&&`. Chain commands with `;` instead.

# The project

## Goal

A weekly model that rotates among the 11 SPDR sector ETFs (XLK, XLE, XLF, XLV, XLI, XLP, XLY, XLB, XLRE, XLU, XLC). Using data through each Friday's close, it predicts for every sector how far that sector will beat or trail SPY over the coming week. The predictions are ranked and the top 3 are held equal weight for one week.

The user is new to quant finance and has completed a graduate data mining course. Keep the scope manageable and the learning curve low.

Everything actually decided — timing, data, features, model, evaluation — is in the decisions log below, which is the only place a decision counts. Nothing else in this file restates those decisions, so there is nowhere for them to drift apart.

## Data status

The `prices` table holds all 11 sectors plus SPY from Tiingo (end-of-day, `adjClose`, daily bars) and 3 FRED series in the same long format, with the FRED series id sitting in the `ticker` column. The `adj_open` column exists on the table and is NULL on all 110,704 rows — nothing has been re-pulled into it yet.

Row counts and date ranges as of the last pull:

| Ticker | Rows | Range |
|---|---|---|
| `DGS10` | 16,129 | 1962-01-02 to 2026-07-30 |
| `DGS2` | 12,537 | 1976-06-01 to 2026-07-30 |
| `BAMLH0A0HYM2` | 7,725 | 1996-12-31 to 2026-07-30 |
| `SPY` | 7,178 | 1998-01-02 to 2026-07-17 |
| The 9 original sectors | 6,933 each | 1998-12-22 to 2026-07-17 |
| `XLRE` | 2,708 | 2015-10-08 to 2026-07-17 |
| `XLC` | 2,030 | 2018-06-19 to 2026-07-17 |

The data is stale. Equities end 2026-07-17 and FRED ends 2026-07-30, roughly 7 weeks behind. Re-pull before treating any backtest result as meaningful.


## Stages

The order the project gets built in, and where it currently stands. Each stage names what it produces and what to check to know it actually worked — most steps here produce a table that looks correct whether or not it is, so the check matters as much as the build.

**Current position: stage 1, task 4 of 6.** Stage 1 breaks into 6 tasks: (1) add the `adj_open` column, (2) widen `store_rows` to 4 columns, (3) pull `adjOpen` in `fetch_and_store_ticker`, (4) write the `BAMLH0A0HYM2` CSV loader, (5) re-pull everything, (6) verify. Tasks 1 through 3 are done. Nothing in stages 2 through 7 has been started.

The `adjOpen` field name is confirmed against Tiingo's own documentation, which also confirms the CRSP adjustment method. No Tiingo pull has been run since task 3, so `fetch_and_store_ticker` is written but unexercised — task 5 is the first time it runs.

**Stage 1 — Data foundation.** Add the `adj_open` column, change `store_rows` to match, re-pull all 12 Tiingo tickers in full, refresh FRED, and load the CSV. *Check:* `adj_open` is non-NULL for every equity row and NULL for every FRED row; `BAMLH0A0HYM2` still starts 1996-12-31; row counts per ticker match or exceed the counts in Data status above.

**Stage 2 — Features.** Build the 11 columns and write the feature table, keyed on the Friday signal date and the ticker with the fill date alongside. *Check:* XLC's first valid values at 4, 12, and 26 weeks land on 2018-07-20, 2018-09-14, and 2018-12-21; no row exists for a week whose Friday is absent from the daily data; every Group B column holds one identical value across all sectors within a given week.

**Stage 3 — Labels.** Build the fill-open-to-next-fill-open excess return and apply the closed-label rule. *Check:* one sector's return for one week, computed by hand from the raw prices, matches the stored label; the newest labeled week is always exactly one week behind the newest feature week; a week whose Monday is a market holiday fills on the Tuesday.

**Stage 4 — Backtest and baselines.** Build `backtest.py` — fills, holidays, costs, metrics — and run the 3 lines that need no model: SPY buy-and-hold, equal weight across valid sectors, and the momentum baseline. This validates the whole pipeline before the hardest piece exists, and produces the number the model has to beat. *Check:* SPY's annual return over the period is close to a published figure; buy-and-hold shows zero turnover after the first week; a sector held two weeks running incurs no cost.

**Stage 5 — Model.** The walk-forward random forest, the fourth line, and the pass rule evaluated against the momentum baseline. *Check:* no training row's label window ends after the date it is used to predict; two runs with the same seed produce identical results.

**Stage 6 — Live job.** Does not start until stage 5's pass rule has been evaluated. The `predict` subcommand, the picks table, weekly scoring of the previous week's pick, phone notification, failure alerting, and reruns that are safe to repeat.

**Stage 7 — Server.** Does not start until stage 6 works locally. Python and uv on the machine, tokens onto it, timezone, a systemd timer, database backup, and the first clone-and-backfill.

## Decisions log

Decisions are recorded here and nowhere else. When a decision is locked in during a conversation, remind the user to add it here.

### Data and storage

- SQLite, one `prices` table in long format: `(date, ticker, value, adj_open)`, primary key `(date, ticker)`, written with `INSERT OR REPLACE` so repeat writes are idempotent. `value` holds the adjusted close for Tiingo rows and the raw level for FRED rows; `adj_open` holds the adjusted open for Tiingo rows and is NULL for FRED rows. The vague `value` name is kept deliberately — renaming touches every query for no functional gain.
- Equity provider: Tiingo's end-of-day endpoint, storing `adjClose` and `adjOpen`, both back-adjusted for splits and dividends following CRSP guidelines.
- Every run re-pulls the complete history of all 12 Tiingo tickers. Tiingo restates the entire adjusted history when a dividend is paid, so an incremental "fetch since last Friday" would leave old rows on the old adjustment factor and new rows on the new one, producing a fake jump at the seam — 4 fake moves of roughly 0.3% to 0.5% per ticker per year, given quarterly dividends. The current fetch already pulls from `START_DATE` on every call; the rule is not to optimize that away.
- Consequence: a full re-pull rewrites all history, so backtest numbers shift slightly week to week. That is inherent to back-adjusted prices, not a bug, and it means a backtest result is not exactly reproducible later.
- Macro provider: FRED's series/observations endpoint, with its own fetch function because the response shape differs from Tiingo's. Raw levels stored as-is. FRED marks missing days with `"."`; those rows are skipped on parse.
- `data/BAMLH0A0HYM2.csv` is committed to git; `*.db` stays ignored. Any rebuild from scratch loads the CSV.
- `BAMLH0A0HYM2` API truncation: FRED returns only the trailing 3 years or so for this series. Root cause unresolved, likely ICE BofA licensing or a realtime/vintage default. The full 1996-to-present history came from a static CSV snapshot, verified against a separate database snapshot — 6,322 overlapping rows, 0 mismatches, no gap at the join. Committing the CSV and loading it on rebuild closes the previously open item about the fetch being wrong standalone.
- Backfill from inception. `START_DATE` is 1998-01-01 and Tiingo clamps each ticker to its real start. Actual starts in the database: SPY 1998-01-02, the 9 original sectors 1998-12-22, XLRE 2015-10-08, XLC 2018-06-19.
- Store daily bars, resample to weekly in pandas. Volatility is the exception — see the feature section.

### Timing and execution

- Features use data through Friday's close.
- Trades fill at the open of the first trading day after that Friday, found by looking up the next date present in `prices`. This covers Monday holidays without a holiday calendar.
- Positions are held until the open of the following week's first trading day. A sector held two weeks running is not traded.
- The same rule governs the backtest and the live job. The live job runs early Monday, before the open.
- Incomplete final week: the weekly resample emits a row for the current week even when daily data stops mid-week — labeled with the upcoming Friday, filled with the last daily close, lookback windows short by a couple of days. Before use, check whether the last row's Friday exists in the daily data and drop the row if it doesn't. The Monday job is safe by construction; this guards off-schedule runs.

### FRED alignment

- All 3 FRED series (`DGS10`, `DGS2`, `BAMLH0A0HYM2`) are lagged one business day and aligned to the last value on or before the lagged date. No forward-fill across gaps.
- Reason for the Treasury lag: `DGS10` and `DGS2` come from the Fed's H.15 release, which publishes the prior business day's rates around 4:15pm ET. FRED's copy of Friday's value appears Monday afternoon — after the Monday-morning job runs and after the fill. Taking Friday's value would read a number that does not exist at signal time.
- High-yield is the decision for the credit spread. Investment-grade is not under consideration.

### Features, version 1 — 11 columns

Group A, sector-specific, carrying the ranking information:

- Relative momentum against SPY at 4, 12, and 26 weeks. Resample daily to weekly first (`W-FRI`, `.last()`), then `pct_change(n, fill_method=None)`. The order matters: resampling first is what makes `n` mean weeks rather than days. `fill_method=None` stops pandas fabricating 0% returns across the ragged starts of XLRE and XLC, leaving early rows `NaN`. Verified on raw momentum before the switch to relative — XLC's first valid values at 4, 12, and 26 weeks land on 2018-07-20, 2018-09-14, and 2018-12-21.
- Cross-sectional rank of 12-week momentum, 1 being best, running to however many sectors have valid data that week. Kept despite deriving from a column already present, because a rank of 1 means the same thing in a calm year and a crash year while a raw return does not, and the model trains across both. Computable from raw or relative momentum — within a week the two order identically.
- Realized volatility from daily returns over the trailing 20 and 60 trading days, computed on daily data and sampled at each Friday. Not from weekly returns, and not annualized.
- Rolling beta to SPY over the trailing 52 weekly returns.

Group B, common regime, identical across sectors within a week and useful only through interactions:

- Yield-curve slope, 10Y minus 2Y, and its weekly change.
- High-yield OAS, lagged as above.
- SPY above or below its 40-week moving average, 0 or 1.

Dropped, with reasons:

- Raw momentum at 4, 12, 26 weeks. Raw and relative order sectors identically within a week, but that alone does not justify dropping them — the forest trains on all sector-weeks pooled and splits on fixed thresholds, so raw momentum is a genuinely different variable carrying SPY's own return over the window. It is dropped because that is market direction, a Group B signal stored in Group A columns, and the label is already relative to SPY, so market direction can only help through interactions. Version 1 keeps market direction only through the SPY 40-week flag. If that flag proves useless, version 2 adds SPY's own 12-week return as one Group B column rather than 3 disguised ones.
- 10-year yield weekly change. The slope is 10Y minus 2Y, so the slope's weekly change already contains it — the same overlap reason that dropped the 10-year level.
- Still cut: short-term reversal, correlation to SPY, distance from the 52-week high, relative volume, drawdown depth, VIX, cross-sectional dispersion, DXY, oil.
- Deferred to version 2: HMM regime switching, put/call ratio, ISM and other macro releases, fund-flow data, earnings-season dummies, pre-bell news.

XLRE and XLC are never zero-filled. Everywhere a sector count matters — the ranking, the rank feature, the equal-weight benchmark — use only the sectors valid that week.

On sizing: 11 features against roughly 16,000 rows sounds generous and isn't. Within a week all sectors share the Group B values exactly, and the long-lookback features barely move — 26-week momentum overlaps its prior value by 25 of 26 weeks, the 52-week beta by 51 of 52. Counted as non-overlapping windows that is about 56 independent draws for the momentum and 28 for the beta, and a minimum leaf size does not fix it. The trigger to cut further is a large gap between in-sample and out-of-sample results. Judge Group B columns by whether removing them hurts, not by standalone importance — they are expected to look near-worthless alone.

### Feature table

- One row per week per sector, stored in SQLite, keyed on the Friday signal date and the ticker. The fill date is its own column so the backtest does not recompute it.
- The whole table is dropped and rebuilt every run, for the same reason prices are re-pulled in full: appending would mix rows computed from pre- and post-restatement prices.
- The backtest and the live prediction both read from this table.

### Model and validation

- Regression, not classification. The label is the sector's return from fill open to next fill open, minus SPY's return over the same window.
- Rank the predictions each week, hold the top N equal weight. N is a parameter, default 3.
- Random forest with fixed hyperparameters and a fixed seed, so runs are reproducible. No hyperparameter search in version 1. **Open: record the chosen values here once set.**
- XGBoost is not considered until random forest results exist.
- Growing-window walk-forward: train from the start through the newest allowable row, predict the next week, retrain weekly. Never a random split.
- The newest allowable training row is the one whose label window has already closed at signal time. At Friday's close of week t, the row for holding week t has a label ending at the next fill open, which is in the future, so it is excluded — the newest usable row is week t-1. There is a test for this.
- First prediction after 5 years of data, counted from the first week where all features are non-null. Given the 52-week beta and sector starts in December 1998, that lands around January 2005 and leaves about 21 years out-of-sample. Note that 2000 through 2002 falls inside the first training window and is never tested; 2008 and 2020 are both out-of-sample.

### Evaluation

- 4 lines through the same backtest with the same fills and costs: the model, SPY buy-and-hold, equal weight across sectors valid that week rebalanced weekly, and a momentum baseline sorting on 12-week relative momentum and holding the top N with no model.
- Transaction costs: a parameter, default 5 basis points per side, charged only on the portion of the portfolio that changes. The final backtest is run once more at 10 basis points for sensitivity.
- Metrics after costs, for all 4 lines: annual return, annual volatility, Sharpe ratio with the risk-free rate set to zero and labeled as such, maximum drawdown, average weekly turnover, hit rate as the fraction of weeks beating SPY, and return per calendar year.
- Pass rule, fixed before the backtest runs: the model's Sharpe and net annual return both beat the momentum baseline, and the model beats the baseline in more than half the calendar years. Beating SPY but not the baseline means momentum works and the model adds nothing. Underperforming is a valid finding.
- All crisis periods kept — 2000, 2008, 2020 and everything else. No exclusions.
- Output to a git-ignored `results/`, overwritten each run: a CSV of weekly returns per line, the metrics table, and the comparison chart.

### Process

- Stages 6 and 7 — live job, notifications, server — do not start until the backtest has run and the pass rule has been evaluated. See the stage list above.
- Data leakage and date alignment are the easiest ways to get a fake good result. Show the work on any step that touches them, and on the transaction-cost math.

# Working in this repo

## Layout

- `src/sector_rotation/` — the package, src-layout, installed via uv.
  - `config.py` — sector list, start date, and API tokens read from `.env`.
  - `db.py` — SQLite connection and schema.
  - `fetch.py` — the full-history re-pull of the 12 Tiingo tickers, the FRED pull, and the CSV load.
  - `features.py` — builds the Group A and Group B columns and writes the feature table. Empty.
  - `labels.py` — builds the open-to-open excess return and applies the closed-label rule. Empty.
  - `backtest.py` — takes a ranking, applies fills, holidays, and costs, and produces the 4 lines and their metrics. Empty.
  - `model.py` — the walk-forward random forest. Empty.
- `main.py` — the runner, with subcommands `backfill`, `update`, `features`, `backtest`, and `predict`. None of them exist yet.
- `tests/` — covers the steps where a mistake is silent: the FRED one-business-day lag, the Treasury alignment, the closed-label rule, and the holiday fill rule.
- `notebooks/main.ipynb` — prototyping only. Working code moves into the package.
- `data/` — `BAMLH0A0HYM2.csv` is committed and is the only source for the full high-yield spread history. The `.db` files are git-ignored.
- `results/` — backtest output, git-ignored, overwritten on every run.

## Running things

The project uses uv and is pinned to Python 3.12.

```
uv sync                    # install dependencies into .venv
uv run main.py backfill    # build the database from scratch: Tiingo, FRED, and the CSV
uv run main.py update      # re-pull all 12 tickers in full, refresh FRED
uv run main.py features    # drop and rebuild the feature table
uv run main.py backtest    # run the 4 lines, write results/
uv run main.py predict     # this week's picks
```

Data pulls hit the Tiingo and FRED APIs. Both are free tiers, but ask before running a pull that is not obviously needed — a full-history pull of 12 tickers is slow and burns rate limit.

## Things that will bite you

- The full history of `BAMLH0A0HYM2` came from the committed CSV, not the FRED API, which returns only the trailing 3 years. A rebuild that skips the CSV silently truncates the series from 1996 to 2023 with no error.
- The FRED series share the `prices` table with the ETFs. A query that assumes every row is a stock price will pick up yields and spreads too.
- `INSERT OR REPLACE` does not edit a row in place. It deletes the matching row and inserts a new one built only from the columns the statement names, so any column left out comes back as NULL. This is why `store_rows` has to name all 4 columns and why every tuple passed to it must carry 4 values, with FRED passing `None` for the open.
