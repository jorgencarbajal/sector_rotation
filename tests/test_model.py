import pandas as pd

from sector_rotation.model import training_slice

# The closed-label rule is the one mistake in this project that makes a backtest look spectacular rather than broken, so both directions are tested: the week that must be excluded, and the week that must survive.
# A test asserting only the exclusion would pass if the function returned nothing at all.


def _four_weeks() -> pd.DataFrame:
    """
    Builds 4 consecutive Fridays with one row each, labelled by date so the test can name which survived.
    Returns a DataFrame of 4 rows with signal_date and excess_return.
    """

    weeks = pd.to_datetime(["2026-01-02", "2026-01-09", "2026-01-16", "2026-01-23"])
    return pd.DataFrame({"signal_date": weeks, "excess_return": [0.1, 0.2, 0.3, 0.4]})


def test_training_slice_excludes_the_week_before() -> None:
    """
    Checks that a model predicting a week cannot train on the week immediately before it.
    Returns None; fails if the previous week survives, which is training on a label that ends at the opening price the job is about to trade into.
    """

    train = training_slice(_four_weeks(), pd.Timestamp("2026-01-23"))

    # 2026-01-16 is the week before. Its label runs to the Monday after 2026-01-23, which has not happened when the job runs.
    assert pd.Timestamp("2026-01-16") not in set(train["signal_date"])


def test_training_slice_keeps_the_week_two_before() -> None:
    """
    Checks that the cutoff removes exactly one week rather than everything recent.
    Returns None; fails if the week two before is dropped, which would mean throwing away usable data.
    """

    train = training_slice(_four_weeks(), pd.Timestamp("2026-01-23"))

    # 2026-01-09's label closed at the open following 2026-01-16, which is in the past by the time this job runs
    assert pd.Timestamp("2026-01-09") in set(train["signal_date"])
    assert len(train) == 2
