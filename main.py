import os
from dotenv import load_dotenv
from sector_rotation.config import SECTORS, START_DATE
from sector_rotation.fetch import fetch_and_store

load_dotenv()
token = os.environ["TIINGO_TOKEN"]

for ticker in SECTORS:
    n = fetch_and_store(ticker, token, START_DATE)
    print(f"{ticker}: {n} rows")