import os
from dotenv import load_dotenv

load_dotenv()

SECTORS = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLB", "XLRE", "XLU", "XLC"]
START_DATE = "1998-01-01"
TIINGO_TOKEN = os.environ["TIINGO_TOKEN"]
FRED_TOKEN = os.environ["FRED_TOKEN"]