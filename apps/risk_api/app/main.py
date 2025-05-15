from fastapi import FastAPI, HTTPException, Query # type:ignore
from typing import List, Dict
from pydantic import BaseModel # type:ignore
import random
# import httpx

# to this (absolute import)
from app.core.db import lifespan  # type:ignore
from app.core.settings import settings



class Position(BaseModel):
    symbol: str
    allocation: float


class Portfolio(BaseModel):
    positions: List[Position]


# Single FastAPI instance, with lifespan hook
app = FastAPI(
    title="RiskPulse API",
    lifespan=lifespan,
)


# In‑memory store
portfolios: Dict[int, Portfolio] = {}
_next_portfolio_id = 1


@app.get("/health/db", summary="DB health check")
async def db_health() -> dict:
    try:
        # this will throw if not connected
        await app.mongodb_client.admin.command("ping")
    except Exception:
        raise HTTPException(status_code=503, detail="MongoDB not reachable")
    return {"status": "ok", "mongodb": "connected"}


# @app.get("/", summary="Fetch external data safely")
# async def read_root():
#     try:
#         async with httpx.AsyncClient(timeout=5.0) as client:
#             resp = await client.get("https://jsonplaceholder.typicode.com/todos/1")
#             resp.raise_for_status()
#             data = resp.json()
#     except httpx.HTTPStatusError as e:
#         raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
#     except (httpx.RequestError, ValueError) as e:
#         raise HTTPException(status_code=502, detail=str(e))

#     return {"data": data}


@app.post("/portfolio", response_model=int, summary="Save user portfolio")
def save_user_input(portfolio: Portfolio) -> int:
    global _next_portfolio_id
    pid = _next_portfolio_id
    portfolios[pid] = portfolio
    _next_portfolio_id += 1
    return pid


@app.get("/portfolio/{pid}", response_model=Portfolio, summary="Retrieve a saved portfolio")
def read_portfolio(pid: int) -> Portfolio:
    if pid not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolios[pid]


@app.get("/risk/var", summary="Compute Value at Risk for a portfolio")
def compute_value_at_risk(
    pid: int = Query(..., description="ID of the saved portfolio")
) -> dict:
    if pid not in portfolios:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    var_value = 0.05
    return {"portfolio_id": pid, "var": var_value}


@app.get("/price/{symbol}", summary="Get latest price for a symbol")
def get_latest_price(symbol: str) -> dict:
    price = round(random.uniform(10.0, 500.0), 2)
    return {"symbol": symbol, "price": price}
