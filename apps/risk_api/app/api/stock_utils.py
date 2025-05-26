from fastapi import APIRouter #type: ignore
from fastapi.concurrency import run_in_threadpool #type: ignore
import yfinance as yf #type: ignore
from datetime import datetime
import numpy as np #type: ignore
import pandas as pd #type: ignore

router = APIRouter(tags=["market"])

from app.api.schemas import Portfolio


@router.get("/quote/{symbol}", summary="Fetch live quote for a ticker")
async def get_quote(symbol: str):
    # 1) Instantiate the Ticker in a thread, not on the event loop
    # This helper offloads a blocking call into a background thread, so your async function can await it without stalling the loop.
    ticker = await run_in_threadpool(yf.Ticker, symbol.upper())

    # 2) Fetch the info dict also off the event loop
    """
    This line basically tells FastAPI, please take this small function (lambda: ticker.info), run it off on a worker thread, and give me back its return value once it’s done.
    """
    info = await run_in_threadpool(lambda: ticker.info)

    # 3) Return a subset (avoid spamming your clients with 100s of fields)
    return {
        "symbol": symbol.upper(),
        "currentPrice": info.get("currentPrice"),
        "previousClose": info.get("previousClose"),
        "open": info.get("open"),
        "dayHigh": info.get("dayHigh"),
        "dayLow": info.get("dayLow"),
    }


async def calculate_historical_var(
    portfolio: Portfolio,
    confidence_level: float = 0.95,
    start_date: str = "2020-01-01",
    end_date: str = None
) -> float:
    """
    Historical VaR for a portfolio of positions.
    """
    end_date = end_date or datetime.today().strftime("%Y-%m-%d")

    # 1 Extract tickers and weights
    symbols = [pos.symbol.upper() for pos in portfolio.positions]
    allocations = np.array([pos.allocation for pos in portfolio.positions])

    # 2 Download price data off the event loop
    df = await run_in_threadpool(
        yf.download,
        symbols,
        start=start_date,
        end=end_date,
        progress=False,
        threads=False
    )
    # yf returns a MultiIndex if multiple symbols
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df["Close"].to_frame()

    # 3 Compute daily returns and drop any missing days
    returns = close.pct_change().dropna()

    # 4 Compute portfolio returns: weighted sum across columns
    # (each column is one ticker’s return series)
    port_returns = returns.dot(allocations)

    # 5 Historical VaR at the given confidence
    # We negate it so VaR is a positive number representing a loss.
    var_percentile = (1 - confidence_level) * 100
    historical_var = -np.percentile(port_returns, var_percentile)

    return float(historical_var)