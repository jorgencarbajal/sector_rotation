import os
from dotenv import load_dotenv

load_dotenv()

SECTORS: list[str] = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLB", "XLRE", "XLU", "XLC"]

# The 12 tickers pulled from Tiingo: the 11 sectors the model chooses between, plus SPY, which every feature and every label is measured against.
ALL_TICKERS: list[str] = SECTORS + ["SPY"]

# The 3 macro series pulled from FRED. DGS10 minus DGS2 is the yield-curve slope, and BAMLH0A0HYM2 is the high-yield credit spread.
FRED_SERIES: list[str] = ["DGS10", "DGS2", "BAMLH0A0HYM2"]

START_DATE: str = "1998-01-01"
TIINGO_TOKEN: str = os.environ["TIINGO_TOKEN"]
FRED_TOKEN: str = os.environ["FRED_TOKEN"]