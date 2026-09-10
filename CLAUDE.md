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

Type-hint everything. Every function gets annotated parameters and an annotated return, and module-level constants get annotated too. Where a shape repeats — a row tuple, a record — declare a named alias once and use the alias, rather than retyping the tuple at each function.

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

The `prices` table holds all 11 sectors plus SPY from Tiingo (end-of-day, daily bars, `adjClose` in `value` and `adjOpen` in `adj_open`) and 3 FRED series in the same long format, with the FRED series id sitting in the `ticker` column. Of 111,216 rows, `adj_open` is filled on all 74,745 equity rows and NULL on all 36,471 FRED rows.

Row counts and date ranges as of the pull on 2026-09-09:

| Ticker | Rows | Range |
|---|---|---|
| `DGS10` | 16,155 | 1962-01-02 to 2026-09-04 |
| `DGS2` | 12,563 | 1976-06-01 to 2026-09-04 |
| `BAMLH0A0HYM2` | 7,753 | 1996-12-31 to 2026-09-08 |
| `SPY` | 7,214 | 1998-01-02 to 2026-09-08 |
| The 9 original sectors | 6,969 each | 1998-12-22 to 2026-09-08 |
| `XLRE` | 2,744 | 2015-10-08 to 2026-09-08 |
| `XLC` | 2,066 | 2018-06-19 to 2026-09-08 |

The database also holds a `features` table of 14,013 rows by 14 columns and a `labels` table of 14,002 rows by 3, both dropped and rebuilt by `main.py dataset`.

The Treasury series ending 4 days before the equities is the documented one-business-day lag, not a gap. 2026-09-07 was Labor Day, so the newest equity bar is Tuesday 2026-09-08, and Tuesday's Treasury values do not reach FRED until Wednesday afternoon.


## Stages

The order the project gets built in, and where it currently stands. Each stage names what it produces and what to check to know it actually worked — most steps here produce a table that looks correct whether or not it is, so the check matters as much as the build.

**Current position: stage 3, task 5 of 6.**

Task 4 is done — the `features` subcommand is now `dataset` and builds both tables in one run. `main.py --help` lists `backfill`, `update`, `dataset`.

Task 3 is done — `build_label_table` and `write_label_table` produce 14,002 rows by 3 columns (`signal_date`, `ticker`, `excess_return`), running 1998-12-25 to 2026-08-28. Rows with no label are dropped rather than stored, so joining this table against `features` hands back exactly the trainable set. The write path was tested against a throwaway database: two runs give the same count, the round trip preserves every value, the primary key rejects a duplicate, and the NOT NULL on `excess_return` rejects a null.

Task 2 is done — `labels.py` has `opens_at` and `build_labels`, producing 1,497 weeks by the 11 sectors with 14,002 labels present. A hand computation from 4 raw opening prices matches to 10 decimal places: XLK for week 2026-08-28 buys at 185.7750 on 08-31 and sells at 188.6400 on 09-08, SPY moves 767.3300 to 769.0700, giving +0.0131542781 both ways. SPY against itself is exactly 0.0. The newest week 2026-09-04 has 0 labels while 08-28 and 08-21 have 11 each. In 0 weeks is the buy date on or before its own Friday, and in 0 weeks is the sell date on or before the buy date. The 14,002 labels against 14,013 feature rows differ by exactly 11, the newest week's sectors.

Weekly excess returns run a mean of +0.002%, a median of -0.015%, a standard deviation of 2.016%, and extremes of -16.5% and +25.6% — the near-zero centre is what it should be, since the sectors collectively make up the market they are measured against.

Task 1 is done — `load_daily_prices` gained a `column` parameter, defaulting to `value` (the adjusted close) and accepting `adj_open` (the price fills happen at). The opens frame matches the closes frame exactly in shape, index and columns, with 0 date-and-ticker pairs holding one but not the other. Asking for opens on the FRED series returns 0 non-null cells, as it should. The column name is checked against a fixed list before being pasted into the SQL, because SQL will not accept a placeholder in place of a column name — both `'close'` and an injection attempt are rejected. The default still produces the same 14,013-row feature table.

All of stage 2's checks passed against the stored `features` table on 2026-09-09, queried from SQL rather than recomputed: 14,013 rows across 1,446 weeks and 11 sectors, running 1998-12-25 to 2026-09-04. XLC's 3 first-valid momentum dates match. 0 weeks have a regime column that differs across sectors. 0 rows duplicate a signal date and ticker. 0 rows have a fill date on or before their signal date, 0 have a missing one, and every fill date is a real trading day in `prices`. All 1,434 ranked weeks hold 1 through n.

51 signal dates are Fridays the market was closed, and all 51 are identified: 28 Good Fridays covering 1999 through 2026, 4 each of New Year's Day, July 3, July 4, Christmas Eve and Christmas Day, plus 3 one-off closures — 2001-09-14 after the September 11 attacks, 2004-06-11 for Reagan's national day of mourning, and 2026-06-19 for Juneteenth. Those weeks are correct rather than broken: the week ended on the Thursday, and the fill lands on the following Monday.

Task 1 is done — `features.py` has `load_daily_prices` and `to_weekly`, verified against the real database: daily is 7,214 rows by 12 columns, weekly is 1,497 by 12, XLC's first weekly row is 2018-06-22, and no cell before a ticker's inception is 0. The incomplete-final-week rule fired on the first run, dropping a bin labeled 2026-09-11 that held Tuesday 2026-09-08's close.

Task 2 is done — `relative_momentum` returns a dict keyed by window, each value 1,497 weeks by the 11 sectors. All 3 of XLC's first-valid dates match the logged values exactly. SPY's column comes out at 0.0 before being dropped, confirming the rows line up, and a hand-computed XLK value for 2026-09-04 matches the stored one to 12 decimal places.

Task 3 is done — `momentum_rank` ranks the 12-week frame within each week. All 1,434 ranked weeks hold whole numbers 1 through n with no gaps and no ties, and the sector count steps up on 1999-03-19, 2016-01-01, and 2018-09-14, each 12 weeks after the corresponding inception.

Task 4 is done — `realized_volatility` returns a dict keyed by window in trading days, each value 1,497 weeks by the 11 sectors. A hand-computed 20-day standard deviation for XLK on 2026-09-04 matches the stored value to 12 decimal places. The holiday-Friday fallback was confirmed on real data: 2026-04-03 is Good Friday, it appears in the weekly index but not the daily one, and the value used comes from Thursday 2026-04-02. The 60-day estimate moves 0.000589 per week on average against the 20-day one's 0.001582, which is the steadier-estimate reasoning showing up in the numbers.

Task 5 is done — `rolling_beta` returns 1,497 weeks by the 11 sectors. SPY against itself came back between 0.999999999999999 and 1.000000000000048 across 1,445 weeks, and the slope for XLK on 2026-09-04 matches `numpy.polyfit` on the same 52 points to 12 decimal places. Long-run average betas order exactly as they should: XLU 0.54, XLP 0.56, XLRE 0.76, XLV 0.78, XLE 0.92, XLC 0.94, XLB 1.04, XLI 1.05, XLY 1.10, XLF 1.14, XLK 1.19.

Task 6 is done — `align_fred` and `group_b_features` produce 1,497 weeks by 4 columns: `curve_slope`, `curve_slope_change`, `hy_oas`, `spy_above_40w`. `load_daily_prices` gained a `tickers` parameter so the same loader reads the 3 FRED series.

The leakage check passes with room to spare. Across all 4,491 Friday-and-series pairs, the observation used is never dated on or after its own Friday: 4,388 reach back 1 calendar day to the Thursday, 102 reach back 2 days when that Thursday was a holiday, and exactly 1 reaches back 4 days. That worst case of 4 days also settles the "no blind forward-fill across gaps" concern — no value is ever carried further than that, so no cap in code is needed.

The trend flag holds only 0.0 and 1.0 with no filled-in False, first valid 1998-10-02 which is 40 weeks after the frame starts, and sits above the average in 74.3% of weeks.

Task 7 is done — `fill_dates` maps each Friday to the first trading day strictly after it. The gap is 3 calendar days in 1,354 weeks (Friday to Monday), 4 days in 141 (a Monday holiday), and 5 days in 2. In 0 of 1,497 weeks does the fill date equal the Friday, which is the check that the lookahead trap is closed. Labor Day 2026 resolves Friday 2026-09-04 to Tuesday 2026-09-08, and Good Friday 2026-04-03 — a Friday that is not a trading day at all — resolves to Monday 2026-04-06. Truncating the data at a Friday makes the newest week's fill date NaT, which is the normal live case: on Monday morning the day the trade fills has not been recorded yet.

Task 8 is done — `build_feature_table` and `write_feature_table` produce 14,013 rows by 14 columns, running 1998-12-25 to 2026-09-04. The row count matches the number of non-NaN weekly price cells across the 11 sectors exactly, 0 rows duplicate a signal date and ticker, and 0 weeks have a regime column that differs across sectors. XLRE's and XLC's first rows land on 2015-10-09 and 2018-06-22, their first weekly prices. The write path was tested against a throwaway database: running it twice gives the same 14,013 rows, the round trip preserves every numeric value, and the primary key rejects a duplicate insert.

Task 9 is done — `main.py features` drops and rebuilds the table, printing a line per step. That subcommand was renamed to `dataset` in stage 3 task 4. Running it against an empty database raises `no price data found in the prices table - run backfill first` rather than a pandas KeyError. That guard needed a change in `load_daily_prices`: it now reindexes the columns instead of selecting them, so a ticker with no rows comes back as an all-NaN column rather than raising. That is what its docstring already promised, and it lets the caller decide what a missing ticker means.

The first week where all 11 features are present is 1999-12-24, set by the 52-week beta. Five years from there puts the first walk-forward prediction at roughly the end of 2004, which matches the estimate already in the decisions log. 12,792 of the 14,013 rows are fully complete; the rest are real observations missing a column whose window has not filled yet.

XLE currently shows a beta of -0.79, which is real rather than a bug. Its weekly returns correlate -0.41 with SPY's over the trailing 52 weeks, measured independently with `.corr()`, and the value has drifted steadily from -0.63 over 8 weeks rather than spiking. Negative betas are rare but not wrong: 44 of 13,441 sector-weeks, or 0.33%. A rolling one-year beta describes one year, not the sector's character.

Stage 1 is complete. All 4 of its checks passed on 2026-09-09: no equity row has a NULL `adj_open`, no FRED row has a non-NULL one, `BAMLH0A0HYM2` still starts 1996-12-31, and every ticker's row count grew rather than shrank.

`main.py` has 3 of its 5 subcommands written: `backfill`, `update`, and `dataset`. The other 2 are deliberately absent because `backtest.py` and `model.py` are empty — each subcommand gets added when the code behind it exists.

**Stage 1 — Data foundation.** Add the `adj_open` column, change `store_rows` to match, re-pull all 12 Tiingo tickers in full, refresh FRED, and load the CSV. *Check:* `adj_open` is non-NULL for every equity row and NULL for every FRED row; `BAMLH0A0HYM2` still starts 1996-12-31; row counts per ticker match or exceed the counts in Data status above.

**Stage 2 — Features.** Build the 11 columns and write the feature table, keyed on the Friday signal date and the ticker with the fill date alongside. *Check:* XLC's first valid values at 4, 12, and 26 weeks land on 2018-07-20, 2018-09-14, and 2018-12-21; no row exists for a week whose Friday is absent from the daily data; every Group B column holds one identical value across all sectors within a given week.

**Stage 3 — Labels.** Build the fill-open-to-next-fill-open excess return and apply the closed-label rule. *Check:* one sector's return for one week, computed by hand from the raw prices, matches the stored label; the newest labeled week is always exactly one week behind the newest feature week; a week whose Monday is a market holiday fills on the Tuesday.

**Stage 4 — Backtest and baselines.** Build `backtest.py` — fills, holidays, costs, metrics — and run the 3 lines that need no model: SPY buy-and-hold, equal weight across valid sectors, and the momentum baseline. This validates the whole pipeline before the hardest piece exists, and produces the number the model has to beat. *Check:* SPY's annual return over the period is close to a published figure; buy-and-hold shows zero turnover after the first week; a sector held two weeks running incurs no cost.

**Stage 5 — Model.** The walk-forward random forest, the fourth line, and the pass rule evaluated against the momentum baseline. *Check:* no training row's label window ends after the date it is used to predict; two runs with the same seed produce identical results.

**Stage 6 — Live job.** Does not start until stage 5's pass rule has been evaluated. The `predict` subcommand, the picks table, weekly scoring of the previous week's pick, phone notification, failure alerting, and reruns that are safe to repeat.

**Stage 7 — Server.** Does not start until stage 6 works locally. Python and uv on the machine, tokens onto it, timezone, a systemd timer, database backup, and the first clone-and-backfill.

### Stage 2 task list

Ten tasks, in dependency order. Each names what to check before moving on, because a feature computed over a window two days short looks exactly like a correct one.

**1. Load the prices into a daily wide frame and a weekly one.** Read `prices` into a frame with dates down the side and tickers across the top, then resample to `W-FRI` with `.last()` for the weekly version. Both frames are needed: the momentum, rank, and beta columns read the weekly one, and the volatility columns read the daily one. Apply the incomplete-final-week rule here — drop the last weekly row unless its Friday actually appears in the daily data. *Check:* XLC's first weekly row is 2018-06-22, the first Friday on or after its 2018-06-19 start; the last weekly row's Friday exists in the daily frame.

**2. Relative momentum against SPY at 4, 12, and 26 weeks.** Resample first, then `pct_change(n, fill_method=None)`, then subtract SPY's return over the same window. *Check:* XLC's first valid values land on 2018-07-20, 2018-09-14, and 2018-12-21. SPY has history back to 1998, so XLC is still the binding constraint and those dates carry over from the raw-momentum verification.

**3. Cross-sectional rank of 12-week momentum.** Rank the sectors within each week, 1 being best, running to however many have a non-null value that week. *Check:* within any week the ranks are 1 through n with no gaps and no ties. The count steps up 12 weeks after each inception rather than on it, because a sector has no 12-week momentum until it has 12 weeks of prices — 9 sectors from 1999-03-19, 10 from 2016-01-01, and 11 from 2018-09-14.

**4. Realized volatility over the trailing 20 and 60 trading days.** Standard deviation of daily returns, computed on the daily frame, then read off at each Friday. Not resampled first, and not annualized. *Check:* one sector's 20-day figure on one Friday, computed by hand from 20 daily closes, matches the stored value.

**5. Rolling beta to SPY over the trailing 52 weekly returns.** Slope of the sector's weekly returns regressed on SPY's. *Check:* SPY against itself returns 1.0; the slope matches `numpy.polyfit` on the same 52 points. Judge realism on the long-run average per sector, not on any single week — a rolling one-year beta can go negative when a sector decouples from the market, and 44 of 13,441 sector-weeks do. The averages should order defensives low and cyclicals high: XLU 0.54, XLP 0.56, up through XLF 1.14 and XLK 1.19.

**6. The four Group B columns.** Yield-curve slope as `DGS10` minus `DGS2`, that slope's weekly change, the lagged high-yield spread, and the SPY 40-week moving-average flag as 0 or 1. All three FRED series lag one business day and align to the last value on or before the lagged date, with no forward-fill across gaps. *Check:* each Group B column holds one identical value across every sector within a given week; a spot-checked Friday's spread equals the last observation on or before the prior business day.

**7. The fill-date column.** For each Friday, the next date that exists in `prices` — no holiday calendar. *Check:* the Friday before a Monday holiday maps to the Tuesday. 2026-09-04 maps to 2026-09-08 because 2026-09-07 was Labor Day.

**8. Assemble and write the feature table.** Join all 11 columns into one frame keyed on the Friday signal date and the ticker, with the fill date alongside, and drop and rebuild the table on every run. *Check:* no duplicate pair of signal date and ticker; the row count equals the number of weeks times the sectors valid in each.

**9. Add the `features` subcommand to `main.py`.** Third of the five, added now that the code behind it exists. Later renamed to `dataset` in stage 3 task 4, once it built the labels table too.

**10. Run the stage 2 checks end to end.** The three in the stage description above, against the written table rather than against frames in memory.


### Stage 3 task list

Six tasks, in dependency order. Stage 3 is where the project first uses data from *after* the signal date, so the checks matter more here than anywhere so far — a label built one week off looks entirely reasonable and produces a backtest that is quietly wrong.

**1. Let `load_daily_prices` read the opens.** It currently reads `value`, the adjusted close. A `column` parameter lets the same function return `adj_open` instead, which is what fills are priced at. *Check:* the opens frame has the same shape as the closes frame, and no date-and-ticker pair has a close but no open.

**2. Build the label.** For each week and sector, the sector's return from its fill open to the following week's fill open, minus SPY's return over the same two dates. The following week's fill date comes from shifting the fill-date series back by one row. *Check:* one sector's label for one week, computed by hand from 4 raw opens, matches the stored value; every sector's label is NaN in the newest week, because its window has not closed; a label computed for SPY against itself is exactly 0.

**3. Write the labels table.** A `labels` table of its own rather than another column on `features`, keyed on signal date and ticker so the two join cleanly. Separate because features are what was knowable at Friday's close and labels are what happened afterward, and keeping that boundary structural makes it harder to train on a column you should not. *Check:* the primary key rejects a duplicate insert; a round trip through SQLite preserves every value; running it twice gives the same row count.

**4. Rename the `features` subcommand to `dataset` and have it rebuild both tables.** One command for the whole modeling dataset, so the 5-subcommand list stays at 5. This is also where `main.py`, the Layout section and Running things get updated, since until this task the command genuinely only builds one table. *Check:* one run produces both tables from scratch, and running it twice leaves the same row counts.

**5. Add pytest and write the first 4 tests.** They cover the steps where a mistake is silent: the FRED one-business-day lag, the Treasury alignment, the closed-label rule, and the holiday fill rule. *Check:* each test fails when you deliberately break the thing it guards. A test that still passes with the code broken is worth nothing, so this is the check that matters, not the count of passing tests.

**6. Run the stage 3 checks end to end.** Against the stored tables, queried from SQL rather than recomputed. *Check:* every labeled row joins to exactly one feature row; a week whose Monday is a market holiday fills on the Tuesday; the newest labeled week is behind the newest feature week by 1 week when prices extend past the last Friday and by 2 weeks when they stop on it, rather than by a fixed number.


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
- Reason for the credit-spread lag: `BAMLH0A0HYM2` posts to FRED on business-day mornings, around 10:00am ET, carrying the prior business day's value. Friday's spread therefore appears Monday at roughly 10:00am ET — after the Monday-morning job runs and after the 9:30am open. Lagging to Thursday's value uses a number that posted Friday morning, hours before it is needed. Same conclusion as the Treasury lag, different publisher and a different time of day. Corroborated by the 2026-09-09 pull: the series held Tuesday 2026-09-08's value while the H.15 series stopped at Friday 2026-09-04.
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
- Labels live in their own `labels` table, keyed the same way on signal date and ticker, rather than as another column on `features`. Features hold what was knowable at Friday's close; labels hold what happened afterward. Keeping the two tables apart makes that boundary structural instead of a thing to remember, so a query cannot casually train on a column it should not see.
- One subcommand, `dataset`, drops and rebuilds both tables. It replaces the `features` subcommand rather than adding a sixth, and the name stays accurate if a third table ever joins them.

### Model and validation

- Regression, not classification. The label is the sector's return from fill open to next fill open, minus SPY's return over the same window.
- Rank the predictions each week, hold the top N equal weight. N is a parameter, default 3.
- Random forest with fixed hyperparameters and a fixed seed, so runs are reproducible. No hyperparameter search in version 1. **Open: record the chosen values here once set.**
- XGBoost is not considered until random forest results exist.
- Growing-window walk-forward: train from the start through the newest allowable row, predict the next week, retrain weekly. Never a random split.
- The newest allowable training row is the one whose label window has already closed by the moment the job runs. The job runs Monday before the open, so a label ending at that Monday's open is not yet known either. Counting back from the week being predicted: week t's label ends at next week's fill open, week t-1's label ends at *this* Monday's open, which has not printed when the job runs, and week t-2's label ends at last week's fill open, which has. The newest usable training row is week t-2. There is a test for this.
- Worked example, for a job running Monday 2026-09-14 before the open. Week t is Friday 2026-09-11, filling 09-14 and selling 09-21 — unknown. Week t-1 is Friday 2026-09-04, which filled Tuesday 09-08 and sells at 09-14's open, the one about to happen — also unknown. Week t-2 is Friday 2026-08-28, which filled 08-31 and sold 09-08, both in the past. Only t-2 is closed.
- How far the newest labeled week sits behind the newest feature week depends on how far the price data extends, so it is not a fixed number. When prices run past the newest Friday, as they do after a mid-week pull, the gap is 1 week. In real Monday-morning operation the data stops at the previous Friday and the gap is 2 weeks. Both are correct; neither is the invariant to check.
- First prediction after 5 years of data, counted from the first week where all features are non-null. Given the 52-week beta and sector starts in December 1998, that lands around January 2005 and leaves about 21 years out-of-sample. Note that 2000 through 2002 falls inside the first training window and is never tested; 2008 and 2020 are both out-of-sample.

### Evaluation

- 4 lines through the same backtest with the same fills and costs: the model, SPY buy-and-hold, equal weight across sectors valid that week rebalanced weekly, and a momentum baseline sorting on 12-week relative momentum and holding the top N with no model.
- Transaction costs: a parameter, default 5 basis points per side, charged only on the portion of the portfolio that changes. The final backtest is run once more at 10 basis points for sensitivity.
- Metrics after costs, for all 4 lines: annual return, annual volatility, Sharpe ratio with the risk-free rate set to zero and labeled as such, maximum drawdown, average weekly turnover, hit rate as the fraction of weeks beating SPY, and return per calendar year.
- Pass rule, fixed before the backtest runs: the model's Sharpe and net annual return both beat the momentum baseline, and the model beats the baseline in more than half the calendar years. Beating SPY but not the baseline means momentum works and the model adds nothing. Underperforming is a valid finding.
- Feature-freshness diagnostic, to run once stage 4 works: rebuild with the 3 FRED series unlagged, taking each Friday's own value instead of Thursday's, and compare against the lagged build. The unlagged version is not tradeable — Friday's high-yield spread does not post until Monday 10:00am ET — so it is a diagnostic, never a candidate strategy. If the two are indistinguishable, that settles it: neither paying for a real-time ICE feed nor moving the rebalance to Tuesday is worth pursuing.
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
  - `features.py` — builds the Group A and Group B columns and writes the features table.
  - `labels.py` — builds the open-to-open excess return and writes the labels table.
  - `backtest.py` — takes a ranking, applies fills, holidays, and costs, and produces the 4 lines and their metrics. Empty.
  - `model.py` — the walk-forward random forest. Empty.
- `main.py` — the runner, with subcommands `backfill`, `update`, `dataset`, `backtest`, and `predict`. The first 3 exist.
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
uv run main.py dataset     # drop and rebuild the features and labels tables
uv run main.py backtest    # run the 4 lines, write results/
uv run main.py predict     # this week's picks
```

Data pulls hit the Tiingo and FRED APIs. Both are free tiers, but ask before running a pull that is not obviously needed — a full-history pull of 12 tickers is slow and burns rate limit.

## Things that will bite you

- The full history of `BAMLH0A0HYM2` came from the committed CSV, not the FRED API, which returns only the trailing 3 years. A rebuild that skips the CSV silently truncates the series from 1996 to 2023 with no error.
- The FRED series share the `prices` table with the ETFs. A query that assumes every row is a stock price will pick up yields and spreads too.
- SPY is in `ALL_TICKERS` and lands in the same wide frame as the sectors, but it is not one of the 11. Every ranking, every sector count, and the equal-weight benchmark has to exclude it. Leaving it in makes the rank feature run 1 to 12 and quietly puts SPY in the portfolio.
- `INSERT OR REPLACE` does not edit a row in place. It deletes the matching row and inserts a new one built only from the columns the statement names, so any column left out comes back as NULL. This is why `store_rows` has to name all 4 columns and why every tuple passed to it must carry 4 values, with FRED passing `None` for the open.
