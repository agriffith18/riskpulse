from fastapi import FastAPI, HTTPException, Query, Request, status # type:ignore
from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr, Field # type:ignore
from bson import ObjectId

from .core.db import lifespan 
from .core.settings import settings

# TODO: add Cors middleware -> https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
# TODO: considerations for avoiding duplicate portfolios and editing existing portfolios

class Position(BaseModel):
    symbol: str
    allocation: float


class Portfolio(BaseModel):
    positions: List[Position]

class User(BaseModel):
    id: str | None = Field(None, alias="_id")
    """
    Tells Pydantic: “When you see a key named _id in the raw data (the dict you get back from Mongo), map it into my id field.”
    
    Without that, Pydantic would ignore _id because it doesn’t match any field name.
    """
    first_name: str
    last_name: str
    email_address: EmailStr
    portfolios: List[Portfolio]
    
    model_config = ConfigDict(
        populate_by_name=True, # This setting tells Pydantic: “Also allow filling the model by the field’s name (id) if it’s present, and by its alias (_id) when the input dict uses that key.”
        extra="ignore" # drop any other fields
    )

class CreatePortfolioRequest(BaseModel):
    user_id: str
    portfolio: Portfolio


# Single FastAPI instance, with lifespan hook
app = FastAPI(
    title="RiskPulse API",
    lifespan=lifespan,
)


@app.get("/health/db", summary="DB health check", tags=["db check"])
async def db_health() -> dict:
    try:
        # this will throw if not connected
        await app.mongodb_client.admin.command("ping")
    except Exception:
        raise HTTPException(status_code=503, detail="MongoDB not reachable")
    return {"status": "ok", "mongodb": "connected"}


@app.post(
    "/create-user", 
    response_model=User, 
    status_code=status.HTTP_201_CREATED, 
    summary="Create user in database", tags=["user"],
)
async def create_user(request: Request, user: User):
    """Insert a new user document and return the saved record"""
    
    user_cols = request.app.mongodb["users"]
    
    # prevent duplicate emails from being saved
    if await user_cols.count_documents({"email_address": user.email_address}, limit=1):
        raise HTTPException(status_code=409, detail="email already exits")
    
    # Insert
    insert_result = await user_cols.insert_one(user.model_dump()) 
    """
    Usinging model_dump() convert User instance into a plain Python dict for Mongo 
    
    Returns: InsertOneResult object; its .inserted_id property holds the new MongoDB _id (an ObjectId) for the document you just wrote.
    """
    
    #Fetch the newly written documentElement()
    saved_doc = await user_cols.find_one({"_id": insert_result.inserted_id})
    if not saved_doc:
        raise HTTPException(status_code=500, detail="insert failed")
    
    #clean up mongodb's BSON ObjectId for JSON output
    saved_doc["id"] = str(saved_doc.pop("_id"))
    
    return User.model_validate(saved_doc)

@app.post(
    "/portfolio",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new portfolio for an existing user",
    tags=["portfolio"],
)
async def save_user_input(
    request: Request,
    body: CreatePortfolioRequest
) -> str:
    """
    Accepts {"user_id": "...", "portfolio": { positions: [...] }},
    verifies the user exists, then creates a separate portfolio document.
    Returns the new portfolio's ID.
    """
    users_col = request.app.mongodb["users"]
    portfolios_col = request.app.mongodb["portfolios"]

    # Verify user exists
    if not await users_col.count_documents(
        {"_id": ObjectId(body.user_id)}, limit=1
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Insert the portfolio, linking it to the user
    data = body.portfolio.model_dump()
    data["user_id"] = ObjectId(body.user_id)
    result = await portfolios_col.insert_one(data)

    # Return the new portfolio's ID as a string
    return str(result.inserted_id)
   

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
