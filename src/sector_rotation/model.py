import pandas as pd

from sector_rotation.db import get_conn
from sector_rotation.features import FEATURE_COLUMNS

# The random forest settings, fixed on 2026-09-10 before any model was fitted and not to be changed after seeing a result.
# min_samples_leaf is the one that matters: the trainable set is 12,781 rows but its effective size is far smaller, since within a week all 11 sectors share the 4 regime values and 26-week momentum overlaps its previous value by 25 of 26 weeks. Small leaves would memorise that structure. See the decisions log.
FOREST_SETTINGS: dict[str, object] = {
    "n_estimators": 500,
    "max_depth": None,
    "min_samples_leaf": 50,
    "max_features": 1 / 3,
    "random_state": 42,
    "n_jobs": -1,
}

# How many years of data the first model trains on. Those years are never themselves predicted.
WARMUP_YEARS: float = 5.0

# How far back the training data is cut off from the week being predicted, in calendar days.
# 14 rather than 7. The job runs on a Monday morning to trade that day's open, and last week's label ends at exactly that open, which has not printed yet. See the closed-label rule in the decisions log.
CLOSED_LABEL_LAG_DAYS: int = 14


def load_training_data() -> pd.DataFrame:
    """
    Joins the features table to the labels table and keeps only the rows a model can actually learn from.
    Returns a DataFrame of roughly 12,800 rows with signal_date, ticker, the 11 feature columns and excess_return; a row missing any feature or the label is dropped.
    An inner join in SQL already drops the weeks whose holding period has not closed, because those have no row in the labels table at all.
    """

    # Open the database connection, join the two tables on week and sector, close the connection
    # An inner join is what removes the newest week: it has features but no label yet, so it has no match on the labels side.
    feature_list = ", ".join(f"f.{name}" for name in FEATURE_COLUMNS)
    conn = get_conn()
    data = pd.read_sql(
        f"""
        SELECT f.signal_date, f.ticker, {feature_list}, l.excess_return
        FROM features f
        JOIN labels l ON f.signal_date = l.signal_date AND f.ticker = l.ticker
        ORDER BY f.signal_date, f.ticker
        """,
        conn,
        parse_dates=["signal_date"],
    )
    conn.close()

    # Drop any row with a gap in a feature or the label
    # These are real weeks for a sector that had listed but had not yet accumulated a full 52 weeks of returns for the beta, or 26 weeks for the longest momentum window. A forest cannot train on a partial row, and filling the gap would invent data.
    return data.dropna().reset_index(drop=True)


def training_slice(data: pd.DataFrame, week: pd.Timestamp) -> pd.DataFrame:
    """
    Selects the rows a model predicting `week` is allowed to train on, which are those whose label window had already closed by the time the job ran.
    Returns the matching rows of `data`, empty when `week` is early enough that nothing qualifies.
    """

    # Cut the data off 2 weeks before the week being predicted
    # 2 weeks, not 1. The job runs on a Monday morning to trade that day's open, and week t-1's label ends at exactly that open, which has not printed yet. Training on it means training on a number that does not exist.
    # Measured in calendar days rather than in rows, so a week missing from the panel cannot quietly shift the cutoff further back than intended.
    cutoff = week - pd.Timedelta(days=CLOSED_LABEL_LAG_DAYS)
    return data[data["signal_date"] <= cutoff]


def walk_forward_predictions(
    data: pd.DataFrame,
    warmup_years: float = WARMUP_YEARS,
    settings: dict[str, object] | None = None,
    progress_every: int = 100,
) -> pd.DataFrame:
    """
    Refits the forest once per week on everything knowable at the time and predicts that week's sectors, walking forward through the whole history.
    Returns a DataFrame with signal_date, ticker and predicted_excess, one row per sector per predicted week; weeks inside the warmup period get no rows.
    `RandomForestRegressor(**settings)` unpacks the settings dict into keyword arguments, so the values live in one place rather than being repeated at the call.
    """

    from sklearn.ensemble import RandomForestRegressor

    settings = FOREST_SETTINGS if settings is None else settings
    # Use whatever feature columns the frame actually carries, so a caller can drop some to test what they were worth
    features = [c for c in FEATURE_COLUMNS if c in data.columns]

    # List every week in order and work out which of them get a prediction
    # A week is predictable once the data that would have been available at the time spans warmup_years. The first 5 years train the first model and are never themselves predicted.
    weeks = pd.DatetimeIndex(sorted(data["signal_date"].unique()))
    first_week = weeks[0]
    predictable = [w for w in weeks if (w - first_week).days >= warmup_years * 365.25]

    predictions = []
    for count, week in enumerate(predictable, start=1):
        # Take only the rows whose label window had closed by the time a job predicting this week would have run
        train = training_slice(data, week)

        # Fit a forest on everything up to the cutoff and predict this week's sectors
        # The model is thrown away afterwards. Every week gets its own, trained only on what preceded it, which is what makes all 1,000-odd predictions genuinely out of sample.
        forest = RandomForestRegressor(**settings)
        forest.fit(train[features], train["excess_return"])

        week_rows = data[data["signal_date"] == week]
        predictions.append(
            pd.DataFrame({
                "signal_date": week_rows["signal_date"].to_numpy(),
                "ticker": week_rows["ticker"].to_numpy(),
                "predicted_excess": forest.predict(week_rows[features]),
            })
        )

        if progress_every and count % progress_every == 0:
            print(f"  {count} of {len(predictable)} weeks, latest {week.date()}, training on {len(train)} rows")

    return pd.concat(predictions, ignore_index=True)


def write_predictions(table: pd.DataFrame) -> int:
    """
    Drops the predictions table, recreates it, and inserts every row of the given frame.
    Returns the number of rows written; raises sqlite3.IntegrityError if the frame holds two rows with the same signal date and ticker.
    """

    # Drop the table and build it again from scratch, the same treatment features and labels get
    conn = get_conn()
    conn.execute("DROP TABLE IF EXISTS predictions")
    conn.execute("""
        CREATE TABLE predictions (
            signal_date      TEXT NOT NULL,
            ticker           TEXT NOT NULL,
            predicted_excess REAL NOT NULL,
            PRIMARY KEY (signal_date, ticker)
        )
    """)

    # Store the date as text in the same format as every other table, then insert
    stored = table.copy()
    stored["signal_date"] = pd.to_datetime(stored["signal_date"]).dt.strftime("%Y-%m-%d")
    stored.to_sql("predictions", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    return len(stored)
