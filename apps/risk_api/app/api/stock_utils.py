from fastapi import APIRouter #type: ignore
from fastapi.concurrency import run_in_threadpool #type: ignore
import yfinance as yf #type: ignore

router = APIRouter(tags=["market"])

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
