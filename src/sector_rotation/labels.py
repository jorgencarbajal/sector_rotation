import pandas as pd

from sector_rotation.config import SECTORS


def opens_at(opens: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    """
    Looks up every ticker's opening price on the given dates, one date per row of the input.
    Returns a DataFrame indexed the same way `dates` is, with one column per ticker; a row whose date is missing or NaT comes back all NaN.
    `reindex` pulls rows out by label rather than by position, so a date that is not in the frame yields NaN instead of raising.
    """

    # Relabel from fill dates to signal dates so the buy and sell frames share an index and can be divided
    looked_up = opens.reindex(dates.to_numpy())
    looked_up.index = dates.index
    return looked_up


def build_labels(opens: pd.DataFrame, fill_dates: pd.Series) -> pd.DataFrame:
    """
    Computes each sector's return from its fill open to the following week's fill open, minus SPY's return over those same two dates.
    Returns a DataFrame of weeks by the 11 sectors; the newest week is all NaN because its holding period has not finished.
    `shift(-1)` moves every value up one row, so each week's row ends up holding the *following* week's fill date.
    """

    # Line up each week with the fill date that closes its holding period, which is the next week's fill date
    sell_dates = fill_dates.shift(-1)

    # Look up the opening prices on the buy date and on the sell date
    buy = opens_at(opens, fill_dates)
    sell = opens_at(opens, sell_dates)

    # Divide the selling price by the buying price and subtract 1, giving every ticker its return over the week actually held
    returns = sell / buy - 1

    # Subtract SPY's return over the same two dates from every ticker's return
    excess = returns.sub(returns["SPY"], axis=0)

    return excess[SECTORS]
