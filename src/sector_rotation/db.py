import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sector_rotation.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            date   TEXT NOT NULL,
            ticker TEXT NOT NULL,
            value  REAL NOT NULL,
            PRIMARY KEY (date, ticker)
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")