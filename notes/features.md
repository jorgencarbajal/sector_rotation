# Feature Candidates — Weekly ML Sector Rotation

**Project context:** rank the 11 SPDR sector ETFs each Friday close (or Wednesday); label = "did sector X beat SPY over the next week?"; hold top-3 equal-weight.

## Ranking / Feature types
A model that **ranks sectors within a week** can only use ranking information from features that **differ across the 11 sectors** in that week. Ranking = ordering by differences, so a column that's identical across sectors can't sort them.

- **Sector-specific (Group A):** varies across the 11 sectors in a given week.
- **Common / regime (Group B):** identical across all 11 sectors *within* a week (constant down the column), but still varies *week to week*. That across-weeks variation is why it's useful — not for ranking, but as a **regime gate** that changes how Group A features get weighted (e.g. "momentum matters more when VIX is low"). Trees learn these interactions automatically, but each common feature buys far less than a sector-specific one.

---

## Group A — Sector-specific (ranking workhorses)

### 1, 3, 4, 5, 6... (choose between 1 or 3)

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

**(NO) 9. Relative volume**
Measure whether a sector is busier or quieter than its own normal. Take this weeks volume, divide by its trailing-average volume (e.g. 12 weeks).
$$\text{rel\_vol} = \text{this week's volume} / \text{trailing-avg volume}$$
- 1.0 = totally normal week
- 2.0 = twice the usual activity
- 0.5 = unusually quiet

The idea being that big moves backed by a volume surge are more "real" than the same move on thin volume.
Weak candidate, volume signals are mostly intra-day, ETF volume is muddied by creation/redemption (authorized participants create and redeem shares to keep price near NAV).

**(NO) 10. Sector drawdown depth**
Measure how far a sector is sitting below its recent peak. Very similar to #8, except that this window is shorter and moves forward.

---

## Group B — Common / regime (constant across sectors in a week)

### 11, 12, 13, 15

> Reminder: none of these can rank the 11 by themselves. They matter only through interactions with Group A. Add them sparingly.

**(YES) 11. Yield-curve slope (10Y−2Y or 10Y−3M) + weekly change** *(v1)*
The slope is the gap between a long rate and a short rate (e.g. the 10-year Treasury yield minus the 2-year).
- Positive/steep (long >> short): normal; markets pricing growth/expansion.
- Flat ($\approx 0$): late-cycle, uncertainty
- Negative/inverted (short > long): the classic recession-warning shape

We also will keep track of the weekly change in the slope.

**(YES/NO) 12. 10Y level + weekly change** *(v1)*
Overlaps with #11, 11 provides more information. The reason this is important is because rates are a discount rate and cost of capital signal, some sectors are structurally rate-sensitive.

The only thing we are keeping from this feature is the weekly change in the yield.

**(YES) 13. Credit spread**
A credit spread is the extra yield investors demand to hold risky corporate bonds instead of safe Treasuries. Its the market's fear gauge for the debt world.
- Narrow/tight spreads: lenders relaxed, credit flowing, risk-on. Good times.
- Wide/blowing-out spreads: lenders scared, demanding compensation for default risk, risk-off. Stress. The bond market tends to price deterioration before equities do.

This plays into sector rotations. Widening spreads = risk-off = defensive rotation. When credit stress rises...
- Money flees to XLP, XLU, XLV (defensive - stable cash flows)
- XLF gets hit hard (banks are credit exposure, loan books deteriorate)
- High-beta cyclicals (XLY, XLK) lag.

Widening spread $\rightarrow$ the model should discount momentum in cyclicals and lean defensive.

Full history will still need to be obtained somehow. Values are released a business day in the future, careful with data leakage.

**(NO) 14. VIX level + weekly change; optionally VIX term structure (VIX vs VIX3M)**
The stock markets fear gauge.
- Low (~12-15): calm, complacent, risk-on.
- Elevated (~20-30): nervous
- Spiking (40+): panic

Absolute thresholds transfer poorly across regimes in walk-forward.

Risk-on / Risk-off gauge... similar to credit spreads?

**(YES) 15. SPY trend state (e.g. above/below 40-wk MA)**
Simple trend state (200 sma, 0/1 output)

**(NO) 16. Cross-sectional dispersion**
How correlated or divergent the sectors are. Can help decide whether rotating even pays off?

**(NO) 17. Dollar index (DXY) / oil**


---

## Group C — Deferred to v2
HMM regime switching · put/call ratio · ISM / macro releases *(publication-lag landmines)* · fund-flow data · earnings-season dummies.

---