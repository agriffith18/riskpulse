from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List
from pydantic import BaseModel 
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.database import Database
from pymongo.collection import ReturnDocument

from ..core.dependencies import get_db  # a small helper that returns request.app.mongodb
from .stock_utils import get_quote, calculate_historical_var, HistoricalVaRRequest

from app.api.schemas import Portfolio, CreatePortfolioRequest
from app.api.stock_utils import calculate_historical_var, beta_calculation

router = APIRouter(
    tags=["portfolio"],
)

@router.get("/health", summary="DB health check")
async def db_health(db: Database = Depends(get_db)) -> dict:
    try:
        await db.client.admin.command("ping")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB not reachable"
        )
    return {"status": "ok", "mongodb": "connected"}


#create
@router.post(
    "/",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new portfolio for a user",
    tags=["portfolio"]
)
async def create_portfolio(
    body: CreatePortfolioRequest,
    db: Database = Depends(get_db),
) -> str:
    users_col = db["users"]
    portfolios_col = db["portfolios"]
    
    # 1) Verify user exists
    if not await users_col.count_documents(
        {"_id": ObjectId(body.user_id)}, limit=1
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    # 2) Insert the portfolio
    data = body.portfolio.model_dump()
    data["user_id"] = ObjectId(body.user_id)
    result = await portfolios_col.insert_one(data)

    # 3) Return the new portfolio's ID
    return str(result.inserted_id)

# read
@router.get(
    "/id/{portfolio_id}",
    response_model=Portfolio,
    summary="Retrieve a saved portfolio by its ID",
    tags=["portfolio"]
)
async def read_portfolio(
    portfolio_id: str,
    db: Database = Depends(get_db),
) -> Portfolio:
    portfolios_col = db["portfolios"]
    
    # 1) Validate ObjectId format and convert - return 422 for invalid format instead of 500
    try:
        object_id = ObjectId(portfolio_id)
    except InvalidId:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid portfolio ID format")
    
    # 2) Fetch by ObjectId
    saved = await portfolios_col.find_one({"_id": object_id})
    if not saved:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found")

    # 3) Convert _id → id
    saved["id"] = str(saved.pop("_id"))

    # 4) Validate into your Pydantic model & return
    return Portfolio.model_validate(saved)



# update
@router.put(
    "/{portfolio_id}",
    response_model=Portfolio,
    summary="Update a saved portfolio by its ID",
    tags=["portfolio"]
)
async def update_portfolio(
    body: Portfolio,
    portfolio_id: str,
    db: Database = Depends(get_db),
) -> Portfolio:
    portfolios_col = db["portfolios"]

    # 1) Validate ObjectId format and convert - return 422 for invalid format instead of 500
    try:
        object_id = ObjectId(portfolio_id)
    except InvalidId:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid portfolio ID format")

    # 2) Build the update data from the incoming model
    update_data = body.model_dump(exclude_unset=True, by_alias=True)

    # 3) Perform find_one_and_update:
    updated = await portfolios_col.find_one_and_update(
        {"_id": object_id},       
        {"$set": update_data},        
        return_document=ReturnDocument.AFTER,
    )

    # 4) If nothing was found, 404
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )

    # 5) Convert Mongo's _id -> string id
    updated["id"] = str(updated.pop("_id"))

    # 6) Validate & return the updated document
    return Portfolio.model_validate(updated)

@router.delete(
    "/{portfolio_id}",
    response_model=bool,                       
    summary="Delete a portfolio by its ID",
    tags=["portfolio"]
)
async def delete_portfolio(
    portfolio_id: str,
    db: Database = Depends(get_db),            
) -> bool:
    portfolios_col = db["portfolios"]

    # 1) Validate ObjectId format and convert - return 422 for invalid format instead of 500
    try:
        object_id = ObjectId(portfolio_id)
    except InvalidId:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid portfolio ID format")

    if not await portfolios_col.count_documents({"_id": object_id}, limit=1):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Perform the deletion by ObjectId
    result = await portfolios_col.delete_one(
        {"_id": object_id}
    )
    
    #  Returns True if exactly one document was removed
    return result.deleted_count == 1


@router.get("/{portfolio_id}/var", response_model=float)
async def get_portfolio_var(
    portfolio_id: str,
    db: Database = Depends(get_db),
) -> float:
    # 1) Validate ObjectId format and convert - return 422 for invalid format instead of 500
    try:
        object_id = ObjectId(portfolio_id)
    except InvalidId:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid portfolio ID format")
    
    # 2) Fetch portfolio from Mongo
    saved = await db["portfolios"].find_one({"_id": object_id})
    if not saved:
        raise HTTPException(404, "Portfolio not found")

    # 3) Validate into Pydantic
    saved["id"] = str(saved.pop("_id"))
    portfolio = Portfolio.model_validate(saved)

    # 4) Calculate VaR
    var_request = HistoricalVaRRequest(portfolio=portfolio)
    var = await calculate_historical_var(var_request)

    return var

# calls beta function inside stock_utils.py
@router.get("/{portfolio_id}/beta", response_model=float)
async def get_portfolio_beta(
    portfolio_id: str,
    db: Database = Depends(get_db),
) -> float:
    # 1) Validate ObjectId format and convert - return 422 for invalid format instead of 500
    try:
        object_id = ObjectId(portfolio_id)
    except InvalidId:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid portfolio ID format")
    
    saved = await db["portfolios"].find_one({"_id": object_id})
    if not saved:
        raise HTTPException(404, "Portfolio not found")

    saved["id"] = str(saved.pop("_id"))
    portfolio = Portfolio.model_validate(saved)

    beta_value = await beta_calculation(portfolio)
    return beta_value

