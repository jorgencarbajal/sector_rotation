# UNDER CONSTRUCTION

## SRC/sector_rotation

config.py
- Set up a some of global variables and parse the .env file to load the token variables.

db.py
- Two functions, get_conn and init_db.  
    get_conn
    - Creates a db connection object. sqlite3.connect("test.db")  # test.db will be created or opened. db file will be stored inside data folder.
    init_db
    - Create the table if it does not exist. Commit and close the db.

fetch.py
- Three functions: fetch_and_store_ticker, fetch_and_store_fred, and store_rows. This file is mainly for storing raw data into the SQLite database.

