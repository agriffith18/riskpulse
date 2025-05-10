from fastapi import FastAPI, HTTPException, Query # type: ignore
from pydantic import BaseModel #type: ignore
from typing import List, Dict
import random

app = FastAPI()

# In-memory “database”
portfolios: Dict[int, "Portfolio"] = {}
_next_portfolio_id = 1


class Position(BaseModel):
    symbol: str
    allocation: float  # as a fraction or percentage


class Portfolio(BaseModel):
    positions: List[Position]


@app.post("/portfolio", response_model=int, summary="Save user portfolio")
def save_user_input(portfolio: Portfolio) -> int:
    """
    Persist a user’s portfolio (list of {symbol, allocation}).
    Returns a generated portfolio ID.
    """
    global _next_portfolio_id
    pid = _next_portfolio_id
    portfolios[pid] = portfolio
    _next_portfolio_id += 1
    return pid


@app.get("/portfolio/{pid}", response_model=Portfolio, summary="Retrieve a saved portfolio")
def read_portfolio(pid: int) -> Portfolio:
    """
    Look up a portfolio by its ID.
    """
    if pid not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolios[pid]


@app.get("/risk/var", summary="Compute Value at Risk for a portfolio")
def compute_value_at_risk(
    pid: int = Query(..., description="ID of the saved portfolio")
) -> dict:
    """
    Calculates (stub) the Value at Risk for the portfolio identified by `pid`.
    """
    if pid not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    # TODO: Replace with real VaR calculation
    var_value = 0.05  
    return {"portfolio_id": pid, "var": var_value}


@app.get("/price/{symbol}", summary="Get latest price for a symbol")
def get_latest_price(symbol: str) -> dict:
    """
    Returns a mocked latest price for the given ticker symbol.
    """
    # TODO: Integrate real market data API (e.g., AlphaVantage, YahooFinance)
    price = round(random.uniform(10.0, 500.0), 2)
    return {"symbol": symbol, "price": price}
