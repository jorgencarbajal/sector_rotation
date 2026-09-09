import sqlite3
from pathlib import Path

DB_PATH: Path = Path(__file__).resolve().parent.parent.parent / "data" / "sector_rotation.db"

def get_conn() -> sqlite3.Connection:
    """
    Return a db connection object connecting to sector_rotation.db
    """
    return sqlite3.connect(DB_PATH)

def init_db() -> None:
    """
    Creates the prices table when it is missing, and adds the adj_open column when an older database lacks it.
    Returns None; raises sqlite3.OperationalError if the database file cannot be opened or written to.
    The list comprehension `[row[1] for row in ...]` builds a list of column names by pulling field 1 out of every row PRAGMA hands back.
    """

    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            date     TEXT NOT NULL,
            ticker   TEXT NOT NULL,
            value    REAL NOT NULL,
            adj_open REAL,
            PRIMARY KEY (date, ticker)
        )
    """)

    # PRAGMA table_info(prices) returns one row per column of the table;
    columns: list[str] = [row[1] for row in conn.execute("PRAGMA table_info(prices)")]

    if "adj_open" not in columns:
        conn.execute("ALTER TABLE prices ADD COLUMN adj_open REAL")
        print("Added adj_open column to the existing prices table")

    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")