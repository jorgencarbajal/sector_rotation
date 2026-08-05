# sector_rotation

Weekly ML sector-rotation model over the 11 SPDR sector ETFs. Classify "will sector X beat SPY next week?", hold top-3 equal-weight. Research project, not production — correctness of the methodology matters more than engineering polish.

Full spec, feature set, data status, and decisions log: @notes/claude_context.md

Deeper rationale for individual features (why each was kept or cut) lives in `notes/features.md` — read it before adding, removing, or arguing about a feature.

## Commands

`uv` manages everything. Python 3.12, src-layout.

```bash
uv sync                  # install deps
uv run main.py           # data pulls (see note below)
uv run jupyter lab       # notebooks/main.ipynb is the prototyping surface
uv add <pkg>             # never pip install
```

`main.py` is a manual runner, not a pipeline. Its calls are deliberately commented out — uncomment the one you want, run it, re-comment it. Don't "fix" this by adding argparse unless asked.

## Layout

```
src/sector_rotation/
  config.py       SECTORS, START_DATE, tokens from .env
  db.py           get_conn(), init_db() — SQLite at data/sector_rotation.db
  fetch.py        Tiingo (equities) + FRED (macro) → prices table
  features/       base.py (daily→weekly), momentum.py, vol.py, beta.py
main.py           manual runner
notebooks/        prototyping
notes/            spec, decisions log, feature rationale
```

`features/vol.py`, `features/beta.py`, and `features/__init__.py` are empty stubs — not yet written.

## Conventions

- **One table, long format.** Everything — sector prices, SPY, and FRED macro series — goes into `prices (date, ticker, value)`. FRED series ids sit in the `ticker` column. Writes are `INSERT OR REPLACE` so re-runs are idempotent.
- **Always open the DB via `get_conn()`** from `db.py`, which resolves the path relative to the package. Do not hardcode relative paths. `features/base.py` currently does (`"../data/sector_rotation.db"`), which only works from `notebooks/` — fix it if you touch that file.
- **Resample before computing.** Daily → weekly (`W-FRI`, `.last()`) first, *then* `pct_change(n)`. Reversing the order silently makes `n` mean days instead of weeks.
- **`fill_method=None` on every `pct_change`.** XLRE and XLC start late; forward-fill fabricates 0% returns across their ragged start. Early rows should stay NaN.
- Comments explain *why*, not *what*. Match the existing density — the codebase is lightly commented and readable.

## Gotchas that will bite

- **Leakage is the main failure mode.** Signal comes from Friday close, execution is Monday open. Credit spread (`BAMLH0A0HYM2`) publishes a day late, so a Friday signal can only see Thursday's value — lag it one business day, and align to the last value on-or-before that date rather than forward-filling across gaps.
- **`BAMLH0A0HYM2` history does not come from the FRED fetch.** The API only returns the trailing ~3 years. Full 1996→present history was backfilled from a CSV snapshot. A rebuild-from-scratch will silently truncate that series to 3 years unless the CSV is reloaded.
- **The trailing weekly bar is usually incomplete.** Resampling labels the current partial week with its Friday date but uses whatever the last daily close was. It must be dropped before it reaches a signal.
- **Walk-forward validation only.** Never a random train/test split. Include ~5-10 bps/trade costs. Benchmarks are buy-and-hold SPY and equal-weight sectors.

## Working with me

- Challenge my reasoning when it's wrong; I'll do the same to you.
- Be concise. Don't create files unless I ask.
- On error-prone steps — data leakage, date alignment, cost math — slow down and show the work.
- When we lock a decision in chat, remind me to add it to the Decisions Log in `notes/claude_context.md`.
- Underperformance vs benchmark is a valid finding, not a failure. Don't tune toward a flattering result.
