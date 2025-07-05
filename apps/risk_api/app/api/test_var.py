import asyncio
import pandas as pd # type: ignore
from fastapi.concurrency import run_in_threadpool # type: ignore
from typing import List
from datetime import datetime
import yfinance as yf #type: ignore


# Bring in the VaR function from stock_utils:
from .stock_utils import calculate_historical_var, beta_calculation

# Import the Pydantic models from portfolio.py (where they actually live):
from .schemas import Portfolio, Position


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
    # 1) Define a toy portfolio to test with:
    portfolio = Portfolio(
        positions=[
            Position(symbol="AAPL", allocation=0.6),
            Position(symbol="MSFT", allocation=0.4),
        ]
    )

    # --------------------------------------
    # Part A: Inspect the raw price DataFrame
    # --------------------------------------
    print("▶️  Fetching raw price DataFrame for AAPL, MSFT…")
    raw_df: pd.DataFrame = await run_in_threadpool(
        fetch_price_frame,
        [p.symbol for p in portfolio.positions],
        "2020-01-01",                      # start_date
        None                               # end_date → defaults to today
    )
    print("\n--- RAW DataFrame head ---")
    print(raw_df.head())

    # Extract the 'Close' column(s) uniformly:
    if isinstance(raw_df.columns, pd.MultiIndex):
        close_df = raw_df["Close"]
    else:
        close_df = raw_df["Close"].to_frame()

    print("\n--- Close prices head ---")
    print(close_df.head())

    # --------------------------------------
    # Part B: Call calculate_historical_var
    # --------------------------------------
    print("\n▶️  Calculating Historical VaR (95%)…")
    var_95 = await calculate_historical_var(portfolio)
    print(f"95% Historical VaR = {var_95:.2%}")

    # --------------------------------------
    # Part C: Call beta_calculation
    # --------------------------------------
    print("\n▶️  Calculating portfolio beta vs S&P 500…")
    beta_val = await beta_calculation(portfolio)
    print(f"Portfolio Beta (vs S&P 500) = {beta_val:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
    