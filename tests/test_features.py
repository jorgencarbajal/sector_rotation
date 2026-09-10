import pandas as pd

from sector_rotation.features import align_fred, fill_dates

# These tests build their own tiny frames rather than reading the database. Real data is slow, and every `update` re-pulls history and shifts the values, so a test asserting a real number would start failing for reasons that have nothing to do with the code.
# Invented data also lets a test build a situation you cannot wait for, such as a Friday the market was closed.


def test_align_fred_reads_thursday_not_friday() -> None:
    """
    Checks that reading a FRED series as of a Friday returns the Thursday value, which is the newest one published by the time the Monday job runs.
    Returns None; fails if the alignment returns Friday's own value, which would be reading a number that does not exist yet.
    """

    # Build 3 consecutive days with a different value on each, then ask for the Friday
    fred = pd.DataFrame(
        {"DGS10": [3.0, 4.0, 9.9]},
        index=pd.to_datetime(["2026-01-07", "2026-01-08", "2026-01-09"]),
    )
    friday = pd.DatetimeIndex(["2026-01-09"])

    aligned = align_fred(fred, friday)

    # 4.0 is Thursday's value; 9.9 is Friday's own and would mean the lag is gone
    assert aligned.loc["2026-01-09", "DGS10"] == 4.0


def test_align_fred_walks_back_past_a_missing_thursday() -> None:
    """
    Checks that when the Thursday has no observation, the alignment falls back to the newest earlier one rather than giving up or jumping forward.
    Returns None; fails if it returns NaN or Friday's own value.
    """

    # Build the same 3 days with the Thursday removed, as if it had been a holiday
    fred = pd.DataFrame(
        {"DGS10": [3.0, 9.9]},
        index=pd.to_datetime(["2026-01-07", "2026-01-09"]),
    )
    friday = pd.DatetimeIndex(["2026-01-09"])

    aligned = align_fred(fred, friday)

    # 3.0 is Wednesday's value, which is what the on-or-before rule should reach
    assert aligned.loc["2026-01-09", "DGS10"] == 3.0


def test_fill_dates_skips_a_closed_monday() -> None:
    """
    Checks that a week's trade fills on the first trading day after the Friday, skipping a Monday the market was closed.
    Returns None; fails if the fill lands on the closed Monday or on the Friday itself.
    """

    # Build a trading calendar that has the Friday and the Tuesday but no Monday, the shape of a Labor Day week
    trading_days = pd.DatetimeIndex(["2026-01-09", "2026-01-13", "2026-01-14"])
    fridays = pd.DatetimeIndex(["2026-01-09"])

    filled = fill_dates(fridays, trading_days)

    # 2026-01-12 is the missing Monday, so the fill has to land on the Tuesday
    assert filled.loc["2026-01-09"] == pd.Timestamp("2026-01-13")


def test_fill_dates_never_returns_the_signal_friday() -> None:
    """
    Checks that a Friday which is itself a trading day is never returned as its own fill date.
    Returns None; fails if the fill equals the Friday, which would mean buying at the open on a signal taken from that same day's close.
    """

    # Build a calendar where every Friday is a trading day, which is the case that a wrong lookup would get wrong
    trading_days = pd.DatetimeIndex(["2026-01-09", "2026-01-12", "2026-01-16", "2026-01-19"])
    fridays = pd.DatetimeIndex(["2026-01-09", "2026-01-16"])

    filled = fill_dates(fridays, trading_days)

    assert (filled.dropna() > filled.dropna().index).all()


def test_align_fred_walks_back_past_a_present_but_empty_thursday() -> None:
    """
    Checks that a Thursday which appears in the frame but holds no reading for this series still falls back to the newest earlier one.
    Returns None; fails if it returns NaN, which is what happens when only the index is walked back and the values are not.
    """

    # Build 3 days where the Thursday row exists but its value is missing, which is what a pivot produces when a different series published that day
    fred = pd.DataFrame(
        {"DGS10": [3.0, None, 9.9]},
        index=pd.to_datetime(["2026-01-07", "2026-01-08", "2026-01-09"]),
    )
    friday = pd.DatetimeIndex(["2026-01-09"])

    aligned = align_fred(fred, friday)

    # 3.0 is Wednesday's value. A NaN here means the row was found and returned with its hole intact.
    assert aligned.loc["2026-01-09", "DGS10"] == 3.0
