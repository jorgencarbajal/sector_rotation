import pandas as pd
import pytest

from sector_rotation.labels import build_labels

# Like the feature tests, these build their own frames. The numbers are chosen so the right answer can be worked out in your head rather than by running the code.


def _opens() -> pd.DataFrame:
    """
    Builds a tiny frame of opening prices on 3 fill dates for one sector and SPY.
    Returns a DataFrame of 3 rows by 2 columns; the numbers are round so the expected returns are exact.
    """

    return pd.DataFrame(
        {
            "XLK": [100.0, 110.0, 121.0],
            "SPY": [100.0, 105.0, 105.0],
        },
        index=pd.to_datetime(["2026-01-12", "2026-01-20", "2026-01-26"]),
    )


def _fills() -> pd.Series:
    """
    Builds the fill dates for 3 Fridays, each landing on the Monday after its Friday.
    Returns a Series of 3 dates indexed by the Friday they belong to.
    """

    fridays = pd.DatetimeIndex(["2026-01-09", "2026-01-16", "2026-01-23"])
    return pd.Series(pd.to_datetime(["2026-01-12", "2026-01-20", "2026-01-26"]), index=fridays)


def test_label_spans_this_weeks_fill_to_next_weeks_fill() -> None:
    """
    Checks that a week's label measures the return from its own fill open to the following week's fill open, minus SPY's return over the same 2 dates.
    Returns None; fails if the label is shifted by a week or measured between the wrong pair of dates.
    """

    labels = build_labels(_opens(), _fills())

    # XLK goes 100 to 110 over the first week, which is +10%; SPY goes 100 to 105, which is +5%; the excess is +5%
    assert labels.loc["2026-01-09", "XLK"] == pytest.approx(0.05)

    # XLK goes 110 to 121 over the second week, which is +10%; SPY is flat at 105, so the excess is the full +10%
    assert labels.loc["2026-01-16", "XLK"] == pytest.approx(0.10)


def test_newest_week_has_no_label() -> None:
    """
    Checks that the most recent week carries no label, because the fill open that would close its holding period has not happened yet.
    Returns None; fails if the newest week gets a number, which would mean the model could train on a week whose outcome is still unknown.
    """

    labels = build_labels(_opens(), _fills())

    assert pd.isna(labels.loc["2026-01-23", "XLK"])
