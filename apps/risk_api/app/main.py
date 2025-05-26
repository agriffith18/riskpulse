from pymongo import AsyncMongoClient
from pymongo.database import Database

from fastapi import FastAPI # type: ignore
from .core.db import lifespan
from .api.portfolio import router as portfolio_router
from .api.portfolio import router as user_router
from .api.stock_utils import router as market_router

app = FastAPI(lifespan=lifespan)
app.include_router(portfolio_router)
app.include_router(user_router)
app.include_router(market_router)

@app.get("/")
async def root():
    return {"message": "Hello from main.py"}

# TODO: add Cors middleware -> https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
# TODO: considerations for avoiding duplicate portfolios and editing existing portfolios

