# app/api/test_var.py
import asyncio
import pandas as pd # type: ignore
from fastapi.concurrency import run_in_threadpool # type: ignore
from typing import List
from datetime import datetime
import yfinance as yf #type: ignore


# 1️⃣ Bring in the VaR function from stock_utils:
from .stock_utils import calculate_historical_var

# 2️⃣ Import the Pydantic models from portfolio.py (where they actually live):
from .schemas import Portfolio, Position

# (And of course your fetch_price_frame helper if you still use it)


def fetch_price_frame(
    symbols: List[str],
    start_date: str = "2020-01-01",
    end_date:   str = None
) -> pd.DataFrame:
    """
    Blocking helper to download and return the historical price DataFrame
    for the given tickers. You would normally wrap this in run_in_threadpool()
    when you call it from async code.
    """
    # 1) If no end_date was provided, default to today’s date
    end_date = end_date or datetime.today().strftime("%Y-%m-%d")

    # 2) Call yfinance.download, which returns a pandas DataFrame
    df = yf.download(
        symbols,            # list of ticker symbols, e.g. ["AAPL","MSFT"]
        start=start_date,   # the start date in "YYYY-MM-DD" format
        end=end_date,       # the end date in "YYYY-MM-DD" format
        progress=False,     # disable yfinance’s progress bar
        threads=False,      # disable yfinance’s internal threading
    )

    # 3) Return that DataFrame to the caller
    return df

async def main():
    # 1) Define a toy portfolio
    portfolio = Portfolio(
        positions=[
            Position(symbol="AAPL", allocation=0.6),
            Position(symbol="MSFT", allocation=0.4),
        ]
    )

    # 2) Pull the raw DataFrame (blocking, so wrap in threadpool)
    raw_df: pd.DataFrame = await run_in_threadpool(
        fetch_price_frame,
        [p.symbol for p in portfolio.positions]
    )

    # 3) Inspect it
    print("--- RAW DataFrame head ---")
    print(raw_df.head())         # shows you all of Open/High/Low/Close/Volume …

    # 4) Drill into Close
    if isinstance(raw_df.columns, pd.MultiIndex):
        close = raw_df["Close"]
    else:
        close = raw_df["Close"].to_frame()

    print("\n--- Close head ---")
    print(close.head())

    # 5) Now call your VaR function
    var_95 = await calculate_historical_var(portfolio)
    print(f"\n95% Historical VaR = {var_95:.2%}")

if __name__ == "__main__":
    asyncio.run(main())
