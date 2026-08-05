import pandas as pd


def build_mom_features(weekly_close, windows=(4, 12, 26)) -> dict[int, pd.DataFrame]:
    """
    Trailing return over each window, keyed by window length in weeks.

    Returns e.g. {4: DataFrame, 12: DataFrame, 26: DataFrame} - one frame per
    window, each the same shape as `weekly_close` (weeks x tickers). A dict
    rather than a tuple so adding a window later cannot break existing callers.

    Steps:
    1. For each window w, pct_change(w) compares every row to the row w
       positions earlier: (price now / price w weeks ago) - 1. That is the
       trailing return. Because rows are already weekly, "w positions back"
       means w weeks back - this is why the input must be resampled first. On
       daily bars the same call would silently mean w *days*.
    2. fill_method=None turns off pandas' default forward-fill. XLRE and XLC
       list later than the other sectors, so their early rows are NaN; with
       fill-on, pandas would copy the first real price backward and report a
       fabricated 0% return. With it off, early rows stay NaN and get dropped
       at training time instead of poisoning the model.
    3. Collect into a dict keyed by w (a dict comprehension - same as building
       an empty dict and assigning result[w] in a loop).
    """
    return {w: weekly_close.pct_change(w, fill_method=None) for w in windows}