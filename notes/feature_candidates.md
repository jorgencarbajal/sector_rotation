# Feature Candidates — Weekly ML Sector Rotation

**Project context:** rank the 11 SPDR sector ETFs each Friday close; label = "did sector X beat SPY over the next week?"; hold top-3 equal-weight. Everything below is judged against *that* task, not generic "is this a good indicator."

## Feature Selection Framework
A model that **ranks sectors within a week** can only use ranking information from features that **differ across the 11 sectors** in that week. Ranking = ordering by differences, so a column that's identical across sectors can't sort them.

- **Sector-specific (Group A):** varies across the 11 sectors in a given week → can rank → these are the workhorses.
- **Common / regime (Group B):** identical across all 11 sectors *within* a week (constant down the column), but still varies *week to week*. That across-weeks variation is why it's useful — not for ranking, but as a **regime gate** that changes how Group A features get weighted (e.g. "momentum matters more when VIX is low"). Trees learn these interactions automatically, but each common feature buys far less than a sector-specific one.

**Division of labor:** *You* decide the menu — which features, how many, and the A:B ratio. The *model* decides how to combine them (including the interactions above). This section exists to guide the menu decisions.

**Target shape (v1):** **8 Group A : 3 Group B, counted as columns** (11 total). Count *columns*, not concepts — the model splits on columns and overfits on columns. Momentum "as one idea" is really 3 columns (4/12/26-wk), so the budget fills fast. This is a starting target, revisable on walk-forward evidence — not a law.

**Feature budget:** ~1,000 weekly rows × 11 sectors, but consecutive weeks overlap heavily (this week's 12-wk momentum shares 11 of 12 weeks with last week's), so the *effective* independent sample is small. Small sample + too many columns → trees memorize noise. Keep it tight. This is a budget, not a wishlist.

**Data cost key:** "free" = computed from ETF/SPY OHLCV you're already pulling from Massive (no new source). Anything needing a new series is called out.

---

## Group A — Sector-specific (ranking workhorses)

**(YES) 1. Momentum — 4/12/26-wk trailing return** *(v1 core)*
This is general momentum. For each sector we will have the return for the last 4, 12, and 26 weeks as independent features.
$$\left(\frac{\text{current price}}{\text{price x-weeks ago}} - 1\right)$$
We need to also consider how we will ensure the price is dividend/split-adjusted close.

**(YES) 2. Relative momentum vs SPY**
Same idea as above except now the formula looks like...
$$\left(\frac{\text{current price}}{\text{price x-weeks ago}} - \frac{\text{spy now}}{\text{spy x-weeks ago}}\right)$$

**(YES) 3. Cross-sectional momentum rank**
Each week, rank the 11 sectors by their momentum (e.g. 12-wk trailing return, or whatever other window size you feel is best). Best = 1 to worst = 11. Same underlying signal as #1, but expressed as within-week *position* instead of *magnitude*. Benefit: a rank means the same thing every week("1 = best of the 11") even when overall market returns swing between calm and crash, so the model can learn a stable rule instead of chasing return values that shift with the regime. Trade-off: discards magnitude (can't tell a runaway leader from a near-tie).

**(NO) 4. Short-term reversal — 1-wk return**
Same math as #1 but within a 1-week window (last Friday → this Friday). The purpose
is different though: over a single week, strong moves tend to partially reverse rather
than continue, so this catches those "buy the dip" moments in a longer up-trending
sector. It's a distinct effect that momentum misses — but it's noisy and often weak on
weekly ETF data, so a strong candidate to get cut once we see the train/OOS gap.

**(YES) 5. Realized volatility — trailing 4/12-wk**
The idea here is to measure the volatility of a sector — the standard deviation of its
weekly returns over a trailing 4 (or 12) week window. This does two things: on its own,
calmer sectors tend to score slightly better risk-adjusted, and more usefully, it lets
the model gauge how much to trust the momentum features — steady momentum is more
believable than momentum from a sector swinging wildly.

**(YES) 6. Sector beta to SPY (rolling)**
Measures how much a sector moves relative to SPY. Beta of 1 = one-to-one (moves the
same amount). Greater than 1 = amplifies SPY's move; less than 1 = dampens it. You get
it by rolling-regressing the sector's weekly returns on SPY's over a trailing window
(plot each week as a dot — SPY return on x, sector return on y — draw the best-fit line;
beta is the slope). "Rolling" = every week, refit that line on the last N weeks and take
the slope. On its own it barely predicts beat-SPY (high beta wins in up weeks but loses
in down weeks, so it washes out); its value is as an interaction partner for the regime
features — it flags which sectors are the aggressive ones, so the model can tilt toward
high-beta in risk-on regimes and low-beta in risk-off.

**(NO) 7. Correlation to SPY (rolling)**
Same scatter plot from #6, just two different questions. Correlation measures how tightly a sector tracks SPY, how reliable they move together, on a scale of -1 to +1.

**(NO) 8. Distance from 52-wk high**
How far the sector has fallen from its own best point over the past year. Take the sectors highest price in the trailing 52 weeks, compare today's price to it.
$$\text{dist} = (\text{current price} / 52\text{week high}) -1$$
This is a strength/health gauge. Highly correlated with #1. Near-highs signals a sector in a confirmed uptrend. Deep-below signals damage.

Where it might earn its own keep — one subtle difference worth knowing: distance-from-high has a ceiling at 0 that raw momentum doesn't. Two sectors can both be "at the top," but one might have +40% raw momentum (rocketed up fast) while the other has +5% (ground up slowly) — yet both read 0 on this feature.

**9. Relative volume**
What: sector's weekly volume vs its own trailing-average volume.
Signal: participation/attention; volume surges can precede or confirm moves.
Type: sector-specific. Data: free.
Role: speculative for a weekly horizon; ETF volume is muddied by creation/redemption. Low priority — test late.

**10. Sector drawdown depth**
What: current % below trailing peak (a continuous, deeper-window cousin of #8).
Signal: risk/stress state of the sector; interacts with mean-reversion vs continuation.
Type: sector-specific. Data: free.
Role: minor; overlaps #8. Probably out for v1.

---

## Group B — Common / regime (constant across sectors in a week)

> Reminder: none of these can rank the 11 by themselves. They matter only through interactions with Group A. Add them sparingly.

**11. Yield-curve slope (10Y−2Y or 10Y−3M) + weekly change** *(v1)*
Signal: curve shape is a classic growth/cycle proxy; steepening vs flattening tilts cyclical vs defensive sectors.
Type: common. Data: Massive Treasury (constant-maturity) — already planned.
Role: primary regime input; cyclicals-vs-defensives is a real sector story.

**12. 10Y level + weekly change** *(v1)*
Signal: rate level/direction drives rate-sensitive sectors (XLU, XLRE) vs others.
Type: common. Data: Massive Treasury.
Role: regime; partly redundant with #11's inputs — decide whether you need both level and slope.

**13. Credit spread** *(v1 — form undecided)*
Signal: widening spreads = risk-off = defensives lead; the cleanest single "financial stress" gauge.
Type: common. Data: **open decision** — HYG/LQD proxy (Massive, full history) vs true OAS (licensed full-history source). Publication-lag/as-of discipline required either way.
Role: high-value regime feature; parked pending the source decision.

**14. VIX level + weekly change; optionally VIX term structure (VIX vs VIX3M)**
Signal: fear gauge → risk-on/off. Term structure (backwardation = acute stress) is often a *stronger* regime flag than the level.
Type: common. Data: Massive Indices (`I:VIX`; check `I:VIX3M`).
Role: core regime input. Consider term structure over raw level if available.

**15. SPY trend state (e.g. above/below 40-wk MA)**
Signal: dead-simple bull/bear switch; momentum and beta behave very differently across it.
Type: common. Data: free (from SPY).
Role: cheap, powerful interaction gate. High value-per-column.

**16. Cross-sectional dispersion**
What: spread between best and worst sector return that week (or stdev across the 11).
Signal: when dispersion is low, rotation has little to capture; high dispersion = more alpha available. A "should I even bet hard this week" meta-signal.
Type: common (one number/week). Data: free (from the 11 sectors).
Role: unusual and cheap; can gate conviction. Worth a test.

**17. Dollar index (DXY) / oil**
Signal: obvious sector tilts — strong USD pressures multinationals/materials; oil drives XLE.
Type: common, but oil is *quasi*-sector-specific through XLE.
Role: oil is the more defensible of the two for sectors; DXY is lower priority. Both are new series — only add if they earn a slot.

---

## Group C — Deferred to v2 (deliberately out now)
HMM regime switching · put/call ratio · ISM / macro releases *(publication-lag landmines)* · fund-flow data · earnings-season dummies.
Reason: each adds a new source, new leakage surface, or new complexity before v1 is even validated. Add only after a clean walk-forward baseline exists.

---

## Practical read for v1
Your original spec = 3 sector-specific vs 4 common features — inverted for a ranking task. The cheapest, highest-leverage upgrade is to deepen **Group A using data you already pull** (#2 relative momentum, #4 reversal, #5 realized vol) *before* adding any new macro series. Then add 2–4 common features (#11/#13/#14/#15) as regime gates. That lands you around 8–12 total, Group-A-weighted, no extra data sources beyond the credit-spread decision.
