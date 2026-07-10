## Goal
- On a weekly basis we will run our "training" and make predictions for each sector on whether they will beat the spy. We pick the top three with the highest prediction. At the end of the week (or maybe midweek...) we will get binary results on whether our selections actually beat the spy. Repeat. When buying the three sectors we will equally spread the position size amongst them.

## ML Choice
- Random Forest then XGBoost: Supervised binary classification. The learning mapping is... features are used to make predictions on whether sectors will beat the spy in the coming week. The features are bundled with the data and the label is binary, 0/1 with 1 meaning this sector beat the spy in the following week. X = features known at Fridays close of week t, y = the forward t->t+1 outcome.
- Training: 

## Features
- 8-12 features is the goal.
- Momentum:
    - We will be taking 3 momentum features per sector 4/12/26 week features. Three columns lets the tree learn interactions like "strong long-term and strong short-term = keep", vs "strong long-term but weak short-term = fading, avoid."
    - 4 week: provides recent/short-term strength (fast noisy)
    - 12 week: "classic" momentum horizon
    - 26 week: longer slower trends

## Phase 0

- Where are you getting the yield curve? Treasury yields, yeild-curve slope, and 10Y level/change. FRED free source?

### Data
- Data source: Tiingo free tier
- Method: re-pull full history each run, no appending (avoids the dividend-restatement seam bug)
- Universe start-data decision: for XLRE AND XLC fill with zeros before their inception dates.

### 11 Sectors
- XLK (Information Technology - 1998) 
- XLC (Communication Services - 1998)
- XLY (Consumer Discretionary - 1998)
- XLP (Consumer Staples - 1998)
- XLE (Energy - 1998)
- XLF (Financials - 1998)
- XLV (Health Care - 1998)
- XLI (Industrials - 1998)
- XLB (Materials - 1998)
- XLRE (Real Estate - 2015)
- XLU (Utilities - 2018)

## Extra things to consider

### Price adjustments
- adjusted prices get retroactively restated. Every time an ETF pays a dividend or splits, the entire prior adjusted-close series is recomputed. So the "append one new row per day" design silently breaks: your old rows were adjusted under yesterday's dividend history, your new row under today's — they're on different scales. Momentum returns computed across that seam are subtly wrong. Classic silent leakage-adjacent bug.

### Dividend adjustments
- Don't "download and hold onto, then append." This is the append-vs-restatement trap — and it bites even with one vendor. When XLU/XLP/XLRE pay quarterly dividends, Tiingo rescales the entire adjusted back-history. Your frozen lump sum won't get that update; your appended weekly bars will — seam bug, again. Fix: re-pull the full 30-yr history on every weekly run (it's ~11 MB and takes seconds, free). No frozen file, no appending, no seam. (Alt for later: store raw/unadjusted OHLCV + divCash/splitFactor and self-adjust — raw prices never get restated so appending is safe. Overkill for now.)

### Trade Costs
- We need to consider the cost of making the trades and how that impacts performance.

### Removing the Fear?
- Do I keep 2000, 2008, 2020. Can these days skew the data in any way?

### Sliding Window
- Should I do a sliding window for the training? Retraining? How to model this sliding window into the training and testing?