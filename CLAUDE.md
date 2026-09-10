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

The database also holds a `features` table of 14,013 rows by 14 columns and a `labels` table of 14,002 rows by 4, both dropped and rebuilt by `main.py dataset`, plus a `predictions` table of 11,081 rows written by the stage 5 walk-forward run.

The Treasury series ending 4 days before the equities is the documented one-business-day lag, not a gap. 2026-09-07 was Labor Day, so the newest equity bar is Tuesday 2026-09-08, and Tuesday's Treasury values do not reach FRED until Wednesday afternoon.


## Stages

The order the project gets built in, and where it currently stands. Each stage names what it produces and what to check to know it actually worked — most steps here produce a table that looks correct whether or not it is, so the check matters as much as the build.

**Current position: stage 5 complete. The model failed the pass rule, and the diagnostics say why. Stages 6 and 7 should not proceed as planned — see the verdict below.**

Task 7 is done, plus 2 diagnostics beyond it.

**Feature importance is almost perfectly flat, which is itself the finding.** Averaged over 21 fits spread across the walk-forward: `rel_mom_12w` 0.130, `rel_mom_26w` 0.124, `rel_mom_4w` 0.122, `beta_52w` 0.121, `vol_20d` 0.107, `hy_oas` 0.106, `vol_60d` 0.104, `curve_slope` 0.094, `curve_slope_change` 0.054, `mom_pct_12w` 0.031, `spy_above_40w` 0.006. An even split across 11 features would be 0.091. Nine of them sit between 0.054 and 0.130 — the forest split on everything roughly equally because nothing was more useful than anything else. The 2 low values are artifacts of how the measure works rather than evidence those columns are worse: impurity importance favours continuous high-cardinality features, and `mom_pct_12w` takes only 9 to 11 distinct values a week while `spy_above_40w` is binary with a single possible split. Group A totals 0.740 against Group B's 0.260, close to the 7-to-4 split you would get from counting columns.

**The model loses in every regime, which kills the version 1 thesis directly.** The bet was that momentum pays inside particular regimes even though it does not on average. Weekly return minus SPY's, sliced by the regime features that were included to detect exactly this:

| slice | weeks | mean vs SPY | standard errors |
|---|---|---|---|
| SPY above its 40-week average | 903 | -6.43 bp | -1.85 |
| SPY below it | 229 | -13.54 bp | -1.16 |
| credit spread tightest third | 380 | -4.34 bp | -0.68 |
| middle third | 378 | -7.88 bp | -1.43 |
| widest third | 374 | -11.45 bp | -1.64 |

Every slice is negative. None is significant on its own, but there is no regime in which this model adds anything.

**The clearest single result: performance improves monotonically as you act on the model less.** Same predictions, no refitting, only the number of sectors held changes:

| held | annual return | Sharpe | max drawdown | turnover |
|---|---|---|---|---|
| top 1 | +5.27% | 0.210 | -64.5% | 53.67% |
| top 3 | +6.05% | 0.314 | -66.0% | 40.37% |
| top 5 | +7.47% | 0.418 | -55.0% | 29.17% |
| top 7 | +9.09% | 0.518 | -54.5% | 17.48% |
| top 9 | +10.04% | 0.588 | -52.9% | 5.26% |
| top 11 | +10.38% | 0.608 | -52.9% | 0.63% |
| SPY | +10.89% | 0.626 | -55.2% | 0.00% |

Every sector added improves both return and Sharpe. At top 11 the model's ranking is doing nothing at all, since holding all 11 is equal weight — and that still trails SPY. The ranking has negative value: the more of it you use, the worse you do, and the best amount to use is none. This is about as conclusive as a backtest gets.

**The 4 regime features were worse than useless.** The decisions log says to judge them by whether removing them hurts rather than by their standalone importance, so a second full walk-forward was run on the 7 Group A features alone.

| features | annual return | Sharpe | max drawdown | turnover |
|---|---|---|---|---|
| all 11 | +6.05% | 0.314 | -66.0% | 40.37% |
| Group A only, 7 | +6.85% | 0.356 | -62.8% | 41.57% |
| SPY | +10.89% | 0.626 | -55.2% | 0.00% |

Removing them **improved** every measure — return, Sharpe and drawdown. They were not merely contributing nothing; on this data they were actively harmful, giving the forest 4 more columns to find spurious structure in. The 2 models' predictions correlate 0.84 and agree on all 3 picks in 415 of 1,132 weeks, so the regime columns did change the picks, just for the worse.

This closes the version 1 thesis completely. The bet was that the regime features would make momentum work by telling the model when to trust it. They did not merely fail to help — the model was better off without them. Neither line comes close to SPY either way.

Task 6 is done. The pass rule was written down before the backtest ran and is applied here unchanged.

**The result, over 2004-12-24 to 2026-08-28:**

| test | bar | model | |
|---|---|---|---|
| annual return | SPY +10.89% | +6.05% | FAIL |
| Sharpe, zero rate | SPY 0.626 | 0.314 | FAIL |
| calendar years beating SPY | 12 of 23 | 7 of 23 | FAIL |

The decisions log says to re-run at 0.75 basis points, the realistic Interactive Brokers floor, before discarding a model that fails at 5. That was done and changes nothing: +7.97% against SPY's +10.90%, Sharpe 0.413 against 0.626, and 10 calendar years of 23. The model fails all 3 tests at both cost levels.

It is also the worst line on risk, not only on return: a 66.0% maximum drawdown against SPY's 55.2%, and 19.31% annual volatility against 17.41%. It turns over 40.4% of itself per week, nearly twice the momentum baseline. It trades the most, earns the least, and falls the furthest.

**Reproducibility, with one honest caveat.** Two runs with the same seed are not bit-identical — they differ by 8.7e-19, or 1.7e-14 in relative terms, because `n_jobs=-1` averages 500 trees in a nondeterministic order. The rankings and the top-3 picks are identical across runs, which is what the backtest depends on. Setting `n_jobs=1` would make it bit-identical at the cost of speed; it has not been changed.

**Where the model did and did not fail.** The per-year table shows it is not uniformly bad: +25.2% against SPY's +10.4% in 2005, +29.1% against +24.9% in 2021. It loses on the big years and on the crash — -42.9% in 2008 against SPY's -33.1%, and -0.9% against +19.3% in 2020. Concentrating into 3 sectors raises the stakes on every pick, and the picks were not good enough to justify it.

Read this together with the stage 4 finding. The 12-week momentum rank carries no unconditional signal, and the model's bet was that momentum pays inside particular regimes. That bet is now tested and lost. The evidence is against the regime interaction as specified in version 1, not against the idea of features in general — but nothing here suggests a small change would rescue it.

Task 5 is done — the model is the 4th line. `momentum_baseline` was renamed `top_n_by_score`, since one function now serves both callers: the baseline hands it the 12-week momentum percentile, the model hands it the predicted excess return. `load_predictions` returns an empty frame when no walk-forward run has happened, so `backtest` simply omits the line.

**Every line is now cut back to the model's period when the model is present.** Without that the model would be judged on 2005 onward while the others carried 1999 onward, and those 6 extra years hold the dot-com crash. The 3 baselines therefore read differently from the stage 4 table: over 2004-12-24 to 2026-08-28 rather than 1998-12-25 to 2026-08-28.

The weights check out: all 1,132 weeks hold exactly 3 sectors at exactly one third each, every row sums to 1, and the picks are the 3 highest predictions. The model holds the same 3 sectors as the momentum baseline in only 25 of 1,132 weeks, 2.2%, so it is genuinely choosing differently rather than reproducing momentum.

**The result, at 5 basis points per side over 2004-12-24 to 2026-08-28:**

| line | annual return | annual vol | Sharpe | max drawdown | avg turnover |
|---|---|---|---|---|---|
| SPY buy-and-hold | **+10.89%** | 17.41% | **0.626** | -55.2% | 0.00% |
| equal weight | +10.32% | 17.06% | 0.605 | -52.9% | 0.63% |
| momentum baseline | +6.54% | 17.05% | 0.383 | -49.7% | 21.66% |
| model | +6.05% | 19.31% | 0.314 | -66.0% | 40.37% |

The model is last of the 4 on return and on Sharpe, and it is the only line with a drawdown worse than SPY's — 66.0% against 55.2%. It also turns over 40.4% of itself per week, nearly twice the momentum baseline, so it trades the most and earns the least. Note that over this period SPY leads equal weight, reversing the stage 4 ordering; the 6 years the restriction removes are what made equal weight look better.

Task 4 is done — the cutoff was inline in the walk-forward loop with nothing a test could address, so it is now `training_slice(data, week)` and `tests/test_model.py` covers it from both directions. 9 tests passing.

Both directions matter. A test asserting only that the previous week is excluded would pass if the function returned nothing at all, so a second test asserts the week two before survives and that exactly 2 of 4 rows do. Mutating the lag proves each catches what it is for: loosening it from 14 days to 7 — the leak itself — fails both tests, and tightening it to 21 fails the second alone. The refactor changed no output: predictions recomputed on a slice match the stored ones to 4.34e-19.

Task 3 is done — `walk_forward_predictions` refits the forest once per week and predicts that week's sectors, and `write_predictions` stores them. 15.2 minutes for 1,132 fits, producing 11,081 predictions from 2004-12-24 to 2026-08-28. The training set grows from 3,231 rows at the start to 13,056 at the end. 261 warmup weeks get no prediction, as intended.

Every check passed. All 1,132 predictable weeks got predictions and no others; every prediction matches a trainable row with 0 spurious and 0 duplicated; and across all 1,132 weeks the smallest gap between a prediction week and its newest training row is exactly 14 days, which is the closed-label rule holding everywhere rather than on the slice it was first checked on.

Two implementation choices worth keeping. The cutoff is measured in calendar days rather than in rows, so a missing week cannot silently shift it — which nearly mattered, since the panel had 67 missing weeks until the `align_fred` fix the same day. And each week gets its own forest which is then discarded, which is what makes every prediction genuinely out of sample and also why this takes a quarter of an hour.

**The predictions carry almost no signal, and this is the result rather than a bug.** Correlation with the actual excess return is -0.0001 across all 11,081 rows. The predictions have a standard deviation of 0.144% against the label's 1.886% — the forest is 13 times less variable than what it is predicting, which is what a model does when it finds little to key on and falls back toward the mean. Whether that still ranks well enough to pick 3 sectors is the question task 5 answers: ranking needs only the ordering to be right, not the magnitude.

**A leakage-adjacent bug in `align_fred` was found on 2026-09-10 while preparing the walk-forward loop, and fixed.** The FRED frame holds 3 series pivoted together, so a date appears in its index whenever *any* of them published. On Thanksgiving 2000 the credit spread had a value and both Treasuries did not, leaving a row that existed with 2 NaN in it. `reindex(method="ffill")` walks back only when the date is missing from the index — the row was there, so it was returned untouched, holes included. That emptied `curve_slope` in 29 weeks and `curve_slope_change` in twice as many, and since the Group B columns are identical across sectors, every affected week lost all 11 rows. The trainable set was 12,781 rows across 1,326 weeks with 67 weeks missing entirely; it is now 13,430 rows across 1,393 weeks with none missing.

The fix is `fred_daily.ffill().reindex(lagged_dates, method="ffill")`. Both steps are needed and they cover different cases: the reindex walks back when the date is absent, the value ffill walks back when the date is present but that series has no reading.

**My stage 2 task 6 verification did not catch this, and the reason is worth remembering.** That check measured staleness with `fred[s].loc[:tgt].last_valid_index()`, which skips NaN — so it measured what the alignment *should* do rather than what `align_fred` returns. It validated a reimplementation. The same blind spot was in the test, which deleted the Thursday row entirely, exercising only the case that already worked. A 7th test now covers a row that is present but empty, and it fails when the fix is reverted. Staleness has been re-measured against the function's actual output: 0 NaN cells across 4,491 lookups, worst reach-back still 4 days.

Any check that reimplements the logic it is checking proves only that two pieces of code agree. Compare against the function, against raw inputs, or against an outside source.

The rank feature became a percentile on 2026-09-10, before the model was fitted — see the decisions log. `momentum_rank` is now `momentum_percentile` and the column is `mom_pct_12w`. Verified: every week's strongest sector scores exactly 1.0 and its weakest exactly 0.0, whatever the sector count, so a 9-sector week and an 11-sector week now sit on one scale. `momentum_baseline` ranks whatever score it is handed rather than reading a stored rank, which is what lets stage 5 pass it the model's predicted excess return instead.

The momentum baseline's numbers are unchanged to the last decimal — largest difference across every metric and every line is 0.0 — which is the check that the change was a relabelling rather than a different strategy. A percentile is a monotone transform of the rank within each week, so the picks could not move.

Task 2 is done — `model.py` has `load_training_data`, joining `features` to `labels` and dropping rows with any gap. 12,781 rows by 14 columns across 1,326 weeks, 1999-12-24 to 2026-08-28, matching the count recorded at the end of stage 3 exactly. 0 NaN cells anywhere. The newest week 2026-09-04 is absent, as it should be — it has features but no label, and the inner join removes it without needing a rule.

The panel is ragged in a way worth remembering: before the `align_fred` fix, 835 weeks carried 9 sectors, 135 carried 10 and 356 carried 11. Nearly two thirds of the training data predates XLRE, so the model spends most of its history choosing among 9. The label centres where an excess return has to: mean +0.008%, median -0.012%, standard deviation 1.99%.

Task 1 is done — scikit-learn 1.9.1 added to the dependencies, and the hyperparameters chosen and written into the decisions log before any model was fitted. Both open decisions settled: predictions get their own table, and the hyperparameters are fixed at 500 trees, no depth limit, 50 samples minimum per leaf, a third of the features per split, seed 42.

Stage 4 is complete.

All of stage 4's checks passed on 2026-09-10.

**The pipeline is exact.** Chaining 1,445 weekly SPY returns gives 10.073264496941; dividing the last fill open by the first gives the same number to 3.55e-15. The 5e-03 gap against the net figure is the one-off entry cost, to 5e-06.

**The data checks out against the outside world.** Tiingo's adjusted closes, compounded over true calendar years, match published S&P 500 total returns with a mean absolute difference of 0.07 points across 1999 to 2025. 22 of the 27 years agree to 0.0; the largest gap is 0.59 points in 2012.

**And it found a real limitation in `returns_by_year`.** It labels a week by its signal Friday, but that week's money moves the following Monday, so each year is shifted by about a week against a published calendar year. Individual years move by up to 6 points — our 2005 reads +10.4% against a published +4.3% — while the 27-year compound stays within 0.07 points, 8.45% against 8.38%. The shift does not touch the pass rule, which compares lines bucketed identically. It does mean a single year from that table must never be quoted against an outside source; compute it from adjusted closes instead. Recorded in the function's docstring.

**Buy-and-hold trades nothing after entry**: turnover 1.0 in week 1, 0.0 across the following 1,444, total lifetime cost 5e-04. **A sector held 2 weeks running with no price move costs exactly 0.**

**The numbers the pass rule measures against**, at 5 basis points per side:

| line | annual return | Sharpe (zero rate) |
|---|---|---|
| SPY buy-and-hold | +8.70% | 0.493 |
| equal weight | **+9.14%** | **0.541** |
| momentum baseline | +5.00% | 0.293 |

Equal weight is the line to beat on both metrics.

**The 12-week momentum rank carries no detectable signal on its own.** Measured on 2026-09-10 across all 13,870 sector-weeks that have both a rank and a label, average weekly excess return against SPY, by rank:

| rank | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| mean % | -0.034 | -0.068 | -0.026 | -0.023 | -0.012 | +0.005 | +0.037 | +0.041 | +0.096 |
| win rate % | 50.3 | 48.3 | 50.2 | 50.6 | 48.4 | 50.0 | 49.4 | 49.1 | 50.7 |

Ranks 10 and 11 have fewer weeks (557 and 416) because they only exist once XLRE and XLC join, so they are not directly comparable.

The best-fit slope across ranks 1 to 11 is +0.011 percentage points per rank — running the wrong way, with weaker momentum doing marginally better. But nothing here is significant: rank 1 sits 0.55 standard errors from zero, rank 2 at 1.28, rank 3 at 0.52, and every win rate is between 48% and 51%. The honest reading is no signal in either direction, not reverse momentum.

Three consequences.

This explains the momentum baseline's failure exactly. It holds 3 sectors that collectively average slightly negative excess return and pays 22% weekly turnover to keep doing it. The loss was not one bad decade — the ranking never had anything in it.

It rules out rank-proportional weighting. Concentrating weight into rank 1 only helps if rank 1 beats rank 2 beats rank 3, and it does not. Adding a weighting knob would have been somewhere to hide rather than a real choice, which is why this was settled with a query rather than by re-running the backtest under several schemes.

And it narrows what stage 5 is actually testing. The measurement above is unconditional, averaged across all 1,433 weeks. The model's bet is that momentum pays only in particular regimes — tight credit spreads, SPY above its 40-week average — and an unconditional average washes exactly that out. That interaction is now the whole thesis rather than one of several, so a stage 5 model that fails should be read as evidence against the interaction specifically, not against the features in general.

Task 7 is done — `main.py backtest` runs the 3 lines, writes the results folder and prints the metrics table, with `--cost-bps` and `--top-n` as options. Running it against a database with no `features` table raises `no features table found - run dataset first` and exits 1 rather than letting SQL complain about a table nobody mentioned. `db.py` gained `table_exists` for that check.

The dispatch table now holds a small function of the parsed arguments per command rather than a bare function, which is what lets `backtest` take options while the other 3 take none. Calling every command with an arguments object it ignores was the alternative.

One ordering mistake: `run_backtest` was appended to the end of the file, after the `if __name__` block, so it was defined too late and the command raised `NameError`. It now sits above `main()`.

Task 6 is done — `write_results` puts 4 files into the git-ignored `results/`: `weekly_returns.csv`, `metrics.csv`, `returns_by_year.csv` and `comparison.png`. A second run overwrites rather than accumulating. matplotlib was added to the dependencies and the renderer is set to `Agg` before pyplot is imported, so the chart draws with no display attached — verified by rendering with `DISPLAY` unset, which is what the server will do under a systemd timer.

The 4 line colours are fixed per line rather than assigned by position, so the 3 existing lines keep their colours when the model line joins them. They are slots 1 to 4 of a palette validated for colourblind separation: worst adjacent pair 9.1 on the protan check against a target of 8. Two of the 4 fall below 3:1 contrast on white, so every line carries a direct label at its right-hand end and identity never rests on colour alone.

Three things were wrong on the first render and fixed after looking at it. Widening the date axis to make room for the labels drew years out to 2032 with no data in them, so the margin is now reserved at the figure level instead. Three translucent drawdown fills stacked in one band were unreadable mud, so drawdowns are drawn as lines. And the log axis was ticking at powers of 10, so it now ticks at 0.5x, 1x, 2x, 5x, 10x.

Task 5 is done — `max_drawdown`, `summarise` and `returns_by_year`. Edge cases check out: a monotone rising series gives a drawdown of exactly 0.0 rather than a floating-point sliver, a flat series gives 0 volatility and a NaN Sharpe rather than dividing by zero, a 100 to 150 to 75 path gives exactly -50%, and per-year returns compound back to the whole-period figure to 12 decimal places.

**The 3 lines, at 5 basis points per side, over 1,445 weeks from 1998-12-25 to 2026-08-28.** Sharpe is the zero-rate figure and must be labeled as such.

| line | annual return | annual vol | Sharpe | max drawdown | avg turnover | hit rate vs SPY | 1 dollar becomes |
|---|---|---|---|---|---|---|---|
| SPY buy-and-hold | +8.70% | 17.64% | 0.493 | -55.2% | 0.00% | — | 10.07x |
| equal weight | +9.14% | 16.89% | 0.541 | -52.9% | 0.68% | 50.2% | 11.24x |
| momentum baseline | +5.00% | 17.04% | 0.293 | -49.7% | 22.03% | 47.5% | 3.86x |

**The line to beat is equal weight on both metrics the pass rule names**: +9.14% annual return and a 0.541 Sharpe. It leads in 14 of the 29 calendar years, SPY in 9, momentum in 6.

All 3 bottomed on 2009-02-27 from an October 2007 peak. Momentum has the shallowest drawdown of the 3 at -49.7%, so its problem is return rather than risk — it gave up 3.7 points a year against SPY without buying any protection for it.

Task 4 is done — `backtest.py` has `load_feature`, `equal_weights`, and the 3 strategies. The SPY line matches `spy_return` exactly with 0 turnover after entry. Equal weight matches the row mean to 2.8e-17. The momentum baseline's picks disagree with "rank 1 through 3 and has a return" in 0 cells out of 15,895, holding exactly 3 sectors in 1,433 of 1,445 weeks. The other 12 are 1998-12-25 through 1999-03-12, before any 12-week rank exists, and hold cash.

**Preliminary result, and it matters for the pass rule.** Rough compounding over the full period, before task 5's proper metrics:

| line | gross CAGR | net at 0.75 bp | net at 5 bp | net at 10 bp | avg weekly turnover |
|---|---|---|---|---|---|
| SPY buy-and-hold | +8.70% | +8.70% | +8.70% | +8.70% | 0.00% |
| equal weight | +9.18% | +9.17% | +9.14% | +9.10% | 0.68% |
| momentum baseline | +6.21% | +6.03% | +5.00% | +3.80% | 22.03% |

The momentum baseline loses to SPY by 3.7 points a year at 5 basis points, and by 2.5 even at the realistic 0.75. Excluding the 12 cash weeks does not rescue it: +5.04% against SPY's +8.56% over the same 1,433 weeks. The gap is not a cost artifact either — it loses by 2.5 points gross.

This inverted the pass rule, which named the momentum baseline as the bar. The rule has been changed to require beating the best of the other 3 lines, measured per metric. See the decisions log.

Cost sensitivity is also concentrated entirely in the momentum line, because it is the only one that trades. Its turnover of 22% a week costs 1.2 points of CAGR between 0.75 and 5 basis points, and 2.4 between 0.75 and 10. SPY moves by 0.004 points across the same range.

A NaN-handling bug in `run_strategy` was found after task 3 and fixed. If a held sector had no return that week, pandas' `skipna` defaults hid it 3 separate times: the gross return summed to 0.0 rather than NaN, the drifted weights renormalised as if that sector did not exist, and the traded amount came back 0.0. The week reported a return of zero and a turnover of zero for a position whose return was unknown, with nothing visible to say so. All 3 row sums now pass `skipna=False`, and the shift of the previous weights uses `fill_value=0.0` rather than `fillna`, which fills only the row shifting vacates instead of also swallowing a real NaN. A week that genuinely holds nothing still zeroes correctly, and the week after a NaN one recovers.

Task 3 is done — `apply_costs` charges the per-side rate against the both-sides traded figure and adds `cost` and `net_return`. It is a separate function rather than a parameter on `run_strategy`, because the same run gets priced at 0.75, 5 and 10 basis points and the gross returns must not move when the cost assumption does. It copies its input, so pricing one run 3 times leaves the original untouched.

All 3 cost cases check out. Holding the same 3 sectors with flat prices costs exactly 0 after entry. Holding the same 3 after one rose 30% costs only the trim: that sector drifts to 0.3939 and the trim is 0.0606 each way, which at 5 basis points is 0.61 bp. Swapping 1 of 3 gives a turnover of exactly one third and costs 3.3333 bp, which is a 10 bp round trip on a third of the portfolio.

Task 2 is done — `backtest.py` has `load_returns` and `run_strategy`. `load_returns` rebuilds every ticker's absolute return from the labels table as `excess_return + spy_return`, giving 1,445 weeks by 12 tickers. `run_strategy` takes target weights and returns gross return, one-way turnover, and the both-sides traded figure the cost is charged on.

Checked on a hand-built 3-week example and against real data. SPY buy-and-hold has a turnover of 1.0 in the entry week and 0.0 in all 1,444 after it, and its gross return equals `spy_return` to floating-point exactness. Equal weight across the valid sectors matches the row mean to 2.8e-17, with an average one-way turnover of 0.68% a week from drift alone. Holding the same sectors with flat prices trades nothing.

Two corrections came out of writing it. Halving the summed weight change to get turnover is wrong in the entry week, where you buy the whole portfolio and sell none of it — buys 1.0 and sells 0.0 halve to 0.5, but the portfolio really did turn over once. Turnover is now the larger of buys or sells, which gives 1.0 on entry and matches the halved sum in every week where the two balance. Separately, a position that outruns the others does not drift as far as it first appears: 0.5 growing 10% against a flat 0.5 lands at 0.5238 rather than 0.55, because the whole portfolio grew.

Task 1 is done — the `labels` table gained a `spy_return` column, giving 14,002 rows by 4. A hand computation from 2 raw SPY opens matches to 12 decimal places. `spy_return` is identical across sectors in 0 weeks out of variance, and `excess_return + spy_return` recovers the sector's absolute return with a worst discrepancy of 0.00e+00 across all 14,002 rows, not just a spot check. The NOT NULL constraint rejects a null. Verified on a copy of the database before you ran it.

Refactoring for this pulled the shared calculation into `holding_period_returns`, which returns every ticker's absolute return over the holding week. `build_labels` and `build_label_table` both read from it, so the excess and SPY numbers come off one frame and cannot drift apart.

All of stage 3's checks passed against the stored tables on 2026-09-10, queried from SQL. `features` holds 14,013 rows to 2026-09-04, `labels` holds 14,002 to 2026-08-28. All 14,002 labels join to a feature row and 0 are orphaned. 3 holiday weeks were spot-checked and each fills on the Tuesday: 2026-09-04 and 2025-08-29 over Labor Day, 2026-01-16 over Martin Luther King Day. 0 labeled weeks have a missing fill date.

The trainable set — rows carrying a label and all 11 features — is 12,781, starting 1999-12-24. That is 11 fewer than the 12,792 complete feature rows, the newest week again.

Task 5 is done — pytest added to the dev dependency group, `tests/test_features.py` and `tests/test_labels.py` written, 6 tests passing in 0.4 seconds with no database involved.

Each test was verified by breaking the behavior it guards and confirming it caught the break. Setting `FRED_LAG_BUSINESS_DAYS` to 0 fails both alignment tests. Changing the alignment from `ffill` to `nearest` fails the walk-back test. Changing `searchsorted` from `side="right"` to `side="left"` fails both fill-date tests. Changing `shift(-1)` to `shift(-2)` fails the label-window test. All 4 mutations were reverted.

Writing the tests found a real inconsistency: `build_labels` ended with `excess[SECTORS]`, which raises when a sector is absent, while `load_daily_prices` had already been changed to `reindex` for that exact reason. `build_labels` now reindexes too. The real pipeline still produces 14,002 label rows.

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

`main.py` has 4 of its 5 subcommands written: `backfill`, `update`, `dataset`, and `backtest`. Only `predict` is absent, because `model.py` is still empty — each subcommand gets added when the code behind it exists.

**Stage 1 — Data foundation.** Add the `adj_open` column, change `store_rows` to match, re-pull all 12 Tiingo tickers in full, refresh FRED, and load the CSV. *Check:* `adj_open` is non-NULL for every equity row and NULL for every FRED row; `BAMLH0A0HYM2` still starts 1996-12-31; row counts per ticker match or exceed the counts in Data status above.

**Stage 2 — Features.** Build the 11 columns and write the feature table, keyed on the Friday signal date and the ticker with the fill date alongside. *Check:* XLC's first valid values at 4, 12, and 26 weeks land on 2018-07-20, 2018-09-14, and 2018-12-21; no row exists for a week whose Friday is absent from the daily data; every Group B column holds one identical value across all sectors within a given week.

**Stage 3 — Labels.** Build the fill-open-to-next-fill-open excess return and apply the closed-label rule. *Check:* one sector's return for one week, computed by hand from the raw prices, matches the stored label; the newest labeled week is always exactly one week behind the newest feature week; a week whose Monday is a market holiday fills on the Tuesday.

**Stage 4 — Backtest and baselines.** Build `backtest.py` — fills, holidays, costs, metrics — and run the 3 lines that need no model: SPY buy-and-hold, equal weight across valid sectors, and the momentum baseline. This validates the whole pipeline before the hardest piece exists, and produces the number the model has to beat. *Check:* SPY's annual return over the period is close to a published figure; buy-and-hold shows zero turnover after the first week; a sector held two weeks running incurs no cost.

**Stage 5 — Model.** The walk-forward random forest, the fourth line, and the pass rule evaluated against the best of the other 3 lines. *Check:* no training row's label window ends after the date it is used to predict; two runs with the same seed produce identical results.

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


### Stage 4 task list

Eight tasks. Stage 4 produces the number the model has to beat, so a backtest that flatters itself here sets the bar too low and every stage 5 result inherits the error.

**1. Add `spy_return` to the labels table.** Computed from the same 2 fill opens as the excess return. *Check:* one week's value hand-computed from 2 raw SPY opens; a sector's absolute return recovered as `excess_return + spy_return` matches the same return computed directly from that sector's own opens.

**2. Turn a weekly set of picks into a weekly return series.** Given which sectors are held each week, produce the portfolio's return for that week and the turnover against the previous week. *Check:* a hand-built 3-week example with known picks gives the returns you can work out on paper; turnover is 0 in a week where the picks did not change.

**3. Apply transaction costs to turnover.** A parameter, default 5 basis points per side, charged on the portion of the portfolio that changes. *Check:* holding the same 3 sectors 2 weeks running with all 3 flat costs exactly 0; holding the same 3 after one of them moved costs only the trimming back to equal weight; replacing 1 of 3 costs the round trip on roughly a third of the portfolio.

**4. Build the 3 strategies that need no model.** SPY buy-and-hold, equal weight across the sectors valid that week rebalanced weekly, and the momentum baseline that sorts on 12-week relative momentum and holds the top N. *Check:* the SPY line's weekly return equals `spy_return` exactly; the equal-weight line equals the mean of that week's sector returns; the momentum baseline's picks are exactly the rows with `mom_rank_12w` of 1 through N.

**5. Compute the metrics.** Annual return, annual volatility, Sharpe with the risk-free rate at zero and labeled as such, maximum drawdown, average weekly turnover, hit rate against SPY, and return per calendar year. *Check:* a constant-return series gives zero volatility and a drawdown of 0 without dividing by zero; a monotone rising series has a drawdown of 0; the per-year returns compound to the whole-period return.

**6. Write the results out.** A CSV of weekly returns per line, the metrics table, and the comparison chart, into the git-ignored `results/`. Adds matplotlib. *Check:* a second run overwrites rather than accumulating; the chart renders without a display attached, which matters for the server later.

**7. Add the `backtest` subcommand.** Fourth of the 5, with the cost in basis points and the number of sectors held as options. *Check:* it runs end to end from a clean `results/`, and exits non-zero when the tables are missing.

**8. Run the stage 4 checks end to end.** *Check:* SPY's annual return over the period is close to a published figure for the same span; buy-and-hold shows zero turnover after the first week; a sector held 2 weeks running incurs no cost. Then record all 3 lines' Sharpe and net annual return in this file, because the best of them per metric is what the pass rule measures the model against.


### Stage 5 task list

Seven tasks. This is the stage the whole project exists to run, and also the one where a mistake is most flattering: a model trained on a label it should not have seen produces a backtest that looks extraordinary and is worth nothing.

**1. Add scikit-learn and record the hyperparameters.** Fixed values and a fixed seed, no search. *Check:* the chosen values are written into the decisions log before any model is fitted, which is what stops them becoming something tuned against the answer.

**2. Load the trainable set.** Join `features` to `labels`, keeping only rows with all 11 features and a label. *Check:* 12,781 rows starting 1999-12-24, matching the count already recorded; no row has a NaN in any feature or in the label.

**3. Run the walk-forward loop.** For each prediction week, train on every row whose label window closed before the job would have run, then predict that week's 11 sectors. Growing window, retrained weekly, first prediction after 5 years of complete rows. *Check:* the first prediction lands around the end of 2004; the number of prediction weeks matches the number of weeks in the trainable set after that date; every predicted week has one value per valid sector.

**4. Test the closed-label rule.** The newest usable training row is week t-2, because week t-1's label ends at the Monday open the job is about to trade into. *Check:* the test fails when the cutoff is loosened to t-1. A test that passes at both cutoffs is not testing anything.

**5. Turn predictions into the fourth line.** Rank each week's predictions, hold the top N equal weight, and run it through the same `run_strategy` and `apply_costs` as the other 3. *Check:* the weights sum to 1 and hold exactly N sectors; the line appears on the chart in the reserved 4th colour without the other 3 changing colour.

**6. Evaluate the pass rule and record the result.** The model's Sharpe and net annual return must both beat equal weight's 0.541 and +9.14%, and beat it in more than half the calendar years. *Check:* two runs with the same seed produce identical predictions to the last decimal. Record the outcome in this file whichever way it goes — underperforming is a valid finding, and the stage 4 result already says the unconditional momentum signal is absent, so a failure here is evidence against the regime interaction specifically rather than against the features in general.

**7. Look at what the model used.** Feature importance across the walk-forward fits, and the Group B columns judged by whether removing them hurts rather than by their standalone importance. *Check:* the Group B columns are expected to look near-worthless alone; the question is whether dropping all 4 changes the result.


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
- Cross-sectional standing in 12-week momentum, stored as `mom_pct_12w`: the fraction of that week's valid sectors this one beat, 1.0 for the strongest and 0.0 for the weakest. Kept despite deriving from a column already present, because a position within the week means the same thing in a calm year and a crash year while a raw return does not, and the model trains across both. Computable from raw or relative momentum — within a week the two order identically.
- It is a percentile rather than the integer rank it started as, changed 2026-09-10. A raw rank does not mean the same thing across the panel: 835 of the 1,326 trainable weeks hold 9 sectors and 356 hold 11, so rank 5 of 9 and rank 5 of 11 are different positions wearing the same number, and the model trains across all of them at once. `(n - rank) / (n - 1)` puts the strongest at exactly 1.0 and the weakest at exactly 0.0 for any n. The alternative considered was training only on weeks with a consistent sector count, which would have discarded 835 weeks to fix a single column.
- The rename from `mom_rank_12w` matters: the column holds 0.0 to 1.0, and leaving the old name on it would have read as a rank. Any earlier note in this file that measures something "by rank" was written against the integer version.
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
- Random forest with fixed hyperparameters and a fixed seed, so runs are reproducible. No hyperparameter search in version 1. Chosen on 2026-09-10, before any model was fitted, and not to be changed after seeing a result: `n_estimators=500`, `max_depth=None`, `min_samples_leaf=50`, `max_features=1/3`, `random_state=42`, `n_jobs=-1`. Fitted with scikit-learn 1.9.1.
- `min_samples_leaf=50` is the one that matters. The trainable set is 12,781 rows but its effective size is far smaller — within a week all sectors share the 4 regime values, and 26-week momentum overlaps its previous value by 25 of 26 weeks. Small leaves would memorise that structure. `max_features=1/3` decorrelates the trees, which is what makes a forest better than one deep tree.
- Searching for hyperparameters is out for version 1, and the reason is worth keeping. Searching once over the whole 27 years and then backtesting on those same years means the settings already know the answer, which is exactly what the walk-forward structure exists to prevent. Searching inside each training window would be leak-free, but it multiplies roughly 1,100 fits by the size of the grid, and aggregating the per-window winners and re-running with them leaks again — that aggregate was chosen knowing every window's outcome. A per-window search is worth running later as a diagnostic of whether the model is stable, never as a way to pick the settings a reported result was produced with.
- Predictions are stored in their own `predictions` table alongside `features` and `labels`. A sector-week's predicted excess return does not depend on how many sectors the portfolio holds, so storing them lets `--top-n` be re-run in seconds rather than refitting the forest 1,100 times.
- XGBoost is not considered until random forest results exist.
- Growing-window walk-forward: train from the start through the newest allowable row, predict the next week, retrain weekly. Never a random split.
- Growing rather than sliding, decided 2026-09-10 with the reasoning below so it is not revisited on instinct. The two are a trade between different errors, not between more and less overfitting. More training data reduces overfitting rather than causing it: with the leaf size fixed at 50 samples, every extra row makes each leaf better supported and memorisation harder, so a model trained on 2,400 rows overfits more than the same model trained on 12,000.
- The real argument for a sliding window is staleness, not overfitting. A growing window means the 2026 model is still shaped by 1999 to 2010, and if the relationship between these features and next week's returns has genuinely changed — different rate regime, different index concentration — that old data is actively misleading rather than merely useless. A sliding window forgets, so it adapts faster.
- Growing wins here on effective sample size, which is the binding constraint in this project. A 5-year sliding window is about 260 weeks, and the 52-week beta overlaps its own previous value by 51 of 52 weeks, so 260 weeks holds roughly 5 genuinely independent observations of that feature. The growing window by 2026 holds about 25. Neither is generous; one is workable and one is not.
- A sliding-window run is worth doing later as a labelled diagnostic of the staleness worry. It is not a second candidate to be chosen between after seeing both results — that is the same trap avoided on the rank-weighting question.
- The newest allowable training row is the one whose label window has already closed by the moment the job runs. The job runs Monday before the open, so a label ending at that Monday's open is not yet known either. Counting back from the week being predicted: week t's label ends at next week's fill open, week t-1's label ends at *this* Monday's open, which has not printed when the job runs, and week t-2's label ends at last week's fill open, which has. The newest usable training row is week t-2. There is a test for this.
- Worked example, for a job running Monday 2026-09-14 before the open. Week t is Friday 2026-09-11, filling 09-14 and selling 09-21 — unknown. Week t-1 is Friday 2026-09-04, which filled Tuesday 09-08 and sells at 09-14's open, the one about to happen — also unknown. Week t-2 is Friday 2026-08-28, which filled 08-31 and sold 09-08, both in the past. Only t-2 is closed.
- How far the newest labeled week sits behind the newest feature week depends on how far the price data extends, so it is not a fixed number. When prices run past the newest Friday, as they do after a mid-week pull, the gap is 1 week. In real Monday-morning operation the data stops at the previous Friday and the gap is 2 weeks. Both are correct; neither is the invariant to check.
- First prediction after 5 years of data, counted from the first week where all features are non-null. Given the 52-week beta and sector starts in December 1998, that lands around January 2005 and leaves about 21 years out-of-sample. Note that 2000 through 2002 falls inside the first training window and is never tested; 2008 and 2020 are both out-of-sample.

### Evaluation

- 4 lines through the same backtest with the same fills and costs: the model, SPY buy-and-hold, equal weight across sectors valid that week rebalanced weekly, and a momentum baseline sorting on 12-week relative momentum and holding the top N with no model.
- Transaction costs: a parameter, default 5 basis points per side, charged only on the portion of the portfolio that changes. The final backtest is run once more at 10 basis points for sensitivity.
- Broker cost structure, from Interactive Brokers' published US commission schedule read on 2026-09-10. IBKR Lite normally charges USD 0.00 commission with no minimum or maximum, but footnote 3 carves out orders that execute in the opening auction: they are free only while they stay under 10% of the account's monthly share volume, and a market order placed before the open is treated as a market-on-open order. This strategy fills every trade at the open, so 100% of its volume falls in that carve-out and it is charged the lesser of USD 0.005 per share or 1% of trade value. The per-share figure binds. For this strategy, IBKR Lite therefore costs the same as IBKR Pro Fixed.
- What that works out to, at opening prices on 2026-09-09: 0.657 basis points per side averaged across the 11 sectors, ranging from 1.161 bp on XLU at USD 43.05 to 0.265 bp on XLK at USD 188.64. Sells add the SEC transaction fee of 0.206 bp; the FINRA activity and audit-trail fees are under 0.02 bp and round away. A round trip on the average sector is therefore about 1.5 basis points in explicit fees, against the 10 basis points a 5-per-side assumption implies.
- The 5 basis points per side stays as the default anyway, because explicit fees are not the whole cost. The bid-ask spread and whatever the opening auction prints away from the quoted mid are not in any fee schedule and are the larger unknown. 5 per side is conservative, which is the safe direction. If the model fails the pass rule at 5, re-run at 0.75 per side before discarding it — that is the realistic floor, and the gap between the two is worth knowing.
- One asymmetry the cost model ignores: a per-share fee costs more in basis points on a cheap ETF than an expensive one, 4.4 times more on XLU than on XLK. Charging a flat rate across all sectors slightly understates the cost of holding the cheap ones.
- Turnover accounts for weight drift. Each week's actual weights, after a week of price moves has pushed them away from equal, are compared against the new target weights, and the cost is charged on the difference. Comparing target to target would see no change when the same sectors are held 2 weeks running and charge nothing, even though the position really was trimmed back to equal weight. That understates costs on every line equally, so it would leave the comparison between them fair while making all the absolute returns better than reality.
- The `labels` table carries a `spy_return` column alongside `excess_return`, computed from the same 2 fill opens. A sector's absolute return is then `excess_return + spy_return`, and SPY's own backtest line is `spy_return` directly. Storing it rather than recomputing it in `backtest.py` keeps 2 numbers that must agree from drifting apart.
- The zero risk-free rate is deliberate and settled. Sharpe here only ranks the 4 lines against each other, and subtracting the same rate from all of them does not change which one leads: equal weight wins at every assumed rate from 0% to 5%. The cost is that the absolute figures come out flattering — SPY's 0.49 would be about 0.38 against a realistic 2% average for this period — which is why the number must always be labeled as a zero-rate Sharpe rather than quoted plainly. Doing it properly would need the 3-month bill (`DTB3`), which is not in `FRED_SERIES`; the 10-year and 2-year already there are the wrong maturity. Only worth adding if a Sharpe is ever quoted outside this project.
- Metrics after costs, for all 4 lines: annual return, annual volatility, Sharpe ratio with the risk-free rate set to zero and labeled as such, maximum drawdown, average weekly turnover, hit rate as the fraction of weeks beating SPY, and return per calendar year.
- Pass rule, fixed before the backtest runs: the model's Sharpe and net annual return both beat the best of the other 3 lines, and the model beats that same line in more than half the calendar years. Best is measured per metric, so the line to beat on Sharpe need not be the line to beat on return.
- The rule originally named the momentum baseline as the bar, written on the assumption that momentum would be the hard target and SPY the easy one. Stage 4 showed the opposite: over 1999 to 2026 the momentum baseline returns about 5% a year against SPY's 8.7%, losing by 2.5 points even before costs. Leaving the rule as written would have let a model pass while losing badly to buying SPY and doing nothing.
- Underperforming every line is a valid finding. So is the stage 4 result on its own: sector momentum did not pay over this period, which is worth knowing whether or not the model works.
- Feature-freshness diagnostic, to run once stage 4 works: rebuild with the 3 FRED series unlagged, taking each Friday's own value instead of Thursday's, and compare against the lagged build. The unlagged version is not tradeable — Friday's high-yield spread does not post until Monday 10:00am ET — so it is a diagnostic, never a candidate strategy. If the two are indistinguishable, that settles it: neither paying for a real-time ICE feed nor moving the rebalance to Tuesday is worth pursuing.
- All crisis periods kept — 2000, 2008, 2020 and everything else. No exclusions.
- Output to a git-ignored `results/`, overwritten each run: a CSV of weekly returns per line, the metrics table, and the comparison chart.

### Process

- Stages 6 and 7 — live job, notifications, server — do not start until the backtest has run and the pass rule has been evaluated. See the stage list above.
- **That gate has now closed against them.** The pass rule was evaluated on 2026-09-10 and the model failed all 3 tests at both cost levels. The gate's purpose was to avoid building deployment infrastructure for a strategy that does not work, and that is exactly the situation. Stages 6 and 7 were deliberately not built. The decision to build them anyway — to accumulate a live paper track record, or to learn the deployment side — belongs to the user and has not been taken.
- If a version 2 is attempted, the stage 4 and stage 5 diagnostics are the place to start, not the model. Sector momentum carries no unconditional signal, the regime interaction that version 1 bet on loses in every regime tested, and performance improves monotonically as the ranking is acted on less. A different model over the same 11 features is very unlikely to change that; a different signal would be needed.
- Data leakage and date alignment are the easiest ways to get a fake good result. Show the work on any step that touches them, and on the transaction-cost math.

# Working in this repo

## Layout

- `src/sector_rotation/` — the package, src-layout, installed via uv.
  - `config.py` — sector list, start date, and API tokens read from `.env`.
  - `db.py` — SQLite connection and schema.
  - `fetch.py` — the full-history re-pull of the 12 Tiingo tickers, the FRED pull, and the CSV load.
  - `features.py` — builds the Group A and Group B columns and writes the features table.
  - `labels.py` — builds the open-to-open excess return and writes the labels table.
  - `backtest.py` — turns weights into weekly returns and turnover, charges costs, builds the no-model strategies, computes the metrics, and writes the results folder.
  - `model.py` — the walk-forward random forest, the settings it is fitted with, the closed-label cutoff, and the predictions writer.
- `main.py` — the runner, with subcommands `backfill`, `update`, `dataset` and `backtest`. `predict` was never built: it belongs to stage 6, which the pass rule gated shut.
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
uv run pytest              # run the tests, under a second, no database needed
uv run main.py dataset     # drop and rebuild the features and labels tables
uv run main.py backtest    # run the lines, write results/  (--cost-bps, --top-n)
uv run main.py predict     # this week's picks
```

Data pulls hit the Tiingo and FRED APIs. Both are free tiers, but ask before running a pull that is not obviously needed — a full-history pull of 12 tickers is slow and burns rate limit.

## Things that will bite you

- The full history of `BAMLH0A0HYM2` came from the committed CSV, not the FRED API, which returns only the trailing 3 years. A rebuild that skips the CSV silently truncates the series from 1996 to 2023 with no error.
- The FRED series share the `prices` table with the ETFs. A query that assumes every row is a stock price will pick up yields and spreads too.
- A schema change leaves a stale `features` table that is present, readable and wrong. Checking the table exists is not enough — the failure surfaces several steps later as SQL complaining about a column the code asked for. `main.py backtest` now checks every name in `FEATURE_COLUMNS` against the stored table and says which one is missing. Any future change to the feature list needs a `dataset` rebuild, and this is what will tell you so.
- SPY is in `ALL_TICKERS` and lands in the same wide frame as the sectors, but it is not one of the 11. Every ranking, every sector count, and the equal-weight benchmark has to exclude it. Leaving it in makes the rank feature run 1 to 12 and quietly puts SPY in the portfolio.
- `INSERT OR REPLACE` does not edit a row in place. It deletes the matching row and inserts a new one built only from the columns the statement names, so any column left out comes back as NULL. This is why `store_rows` has to name all 4 columns and why every tuple passed to it must carry 4 values, with FRED passing `None` for the open.
