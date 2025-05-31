from fastapi import APIRouter, HTTPException, Depends, status # type: ignore
from typing import List
from pydantic import BaseModel # type: ignore
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import ReturnDocument

from ..core.dependencies import get_db  # a small helper that returns request.app.mongodb
from .stock_utils import get_quote, calculate_historical_var

from app.api.schemas import Portfolio, CreatePortfolioRequest
from app.api.stock_utils import calculate_historical_var, beta_calculation

router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
)

#create
@router.post(
    "",
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
    "/{user_id}",
    response_model=Portfolio,
    summary="Retrieve a saved portfolio by its ID",
    tags=["portfolio"]
)
async def read_portfolio(
    user_id: str,
    db: Database = Depends(get_db),
) -> Portfolio:
    portfolios_col = db["portfolios"]

    # 1) Fetch by ObjectId
    saved = await portfolios_col.find_one({"_id": ObjectId(user_id)})
    if not saved:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found")

    # 2) Convert _id → id
    saved["id"] = str(saved.pop("_id"))

    # 3) Validate into your Pydantic model & return
    return Portfolio.model_validate(saved)


# update
@router.put(
    "/{user_id}",
    response_model=Portfolio,
    summary="Update a saved portfolio by its ID",
    tags=["portfolio"]
)
async def update_portfolio(
    body: Portfolio,
    user_id: str,
    db: Database = Depends(get_db),
) -> Portfolio:
    portfolios_col = db["portfolios"]

    # 1) Build the update data from the incoming model
    update_data = body.model_dump(exclude_unset=True, by_alias=True)

    # 2) Perform find_one_and_update:
    updated = await portfolios_col.find_one_and_update(
        {"_id": ObjectId(user_id)},       
        {"$set": update_data},        
        return_document=ReturnDocument.AFTER,
    )

    # 3) If nothing was found, 404
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found",
        )

    # 4) Convert Mongo’s _id -> string id
    updated["id"] = str(updated.pop("_id"))

    # 5) Validate & return the updated document
    return Portfolio.model_validate(updated)

@router.delete(
    "/{user_id}",
    response_model=bool,                       
    summary="Delete a portfolio by its ID",
    tags=["portfolio"]
)
async def delete_portfolio(
    user_id: str,
    db: Database = Depends(get_db),            
) -> bool:
    portfolios_col = db["portfolios"]

    if not await portfolios_col.count_documents({"_id": ObjectId(user_id)}, limit=1):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Perform the deletion by ObjectId
    result = await portfolios_col.delete_one(
        {"_id": ObjectId(user_id)}
    )
    
    #  Returns True if exactly one document was removed
    return result.deleted_count == 1


@router.get("/{user_id}/var", response_model=float)
async def get_portfolio_var(
    user_id: str,
    db: Database = Depends(get_db),
) -> float:
    # 1 Fetch portfolio from Mongo
    saved = await db["portfolios"].find_one({"_id": ObjectId(user_id)})
    if not saved:
        raise HTTPException(404, "Portfolio not found")

    # 2 Validate into Pydantic
    saved["id"] = str(saved.pop("_id"))
    portfolio = Portfolio.model_validate(saved)

    # 3 Calculate VaR
    var = await calculate_historical_var(portfolio)

    return var

# calls beta function inside stock_utils.py
@router.get("/{user_id}/beta", response_model=float)
async def get_portfolio_beta(
    user_id: str,
    db: Database = Depends(get_db),
) -> float:
    saved = await db["portfolios"].find_one({"_id": ObjectId(user_id)})
    if not saved:
        raise HTTPException(404, "Portfolio not found")

    saved["id"] = str(saved.pop("_id"))
    portfolio = Portfolio.model_validate(saved)

    beta_value = await beta_calculation(portfolio)
    return beta_value
