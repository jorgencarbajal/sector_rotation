import os
from dotenv import load_dotenv

load_dotenv()

SECTORS = ["XLK", "XLE", "XLF", "XLV", "XLI", "XLP", "XLY", "XLB", "XLRE", "XLU", "XLC"]
BENCHMARK = "SPY"
# SPY rides through the same resample as the sectors so weekly bars can never
# drift out of alignment. Rank features still use SECTORS - ranking is 11-wide.
UNIVERSE = SECTORS + [BENCHMARK]
START_DATE = "1998-01-01"
TIINGO_TOKEN = os.environ["TIINGO_TOKEN"]
FRED_TOKEN = os.environ["FRED_TOKEN"]