from fastapi import APIRouter, HTTPException, Depends, status # type: ignore
from typing import List
from pydantic import BaseModel # type: ignore
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import ReturnDocument

from ..core.dependencies import get_db  # a small helper that returns request.app.mongodb

class Position(BaseModel):
    symbol: str
    allocation: float


class Portfolio(BaseModel):
    positions: List[Position]


class CreatePortfolioRequest(BaseModel):
    user_id: str
    portfolio: Portfolio



router = APIRouter(
    prefix="/portfolio",
    tags=["portfolio"],
)

@router.post(
    "",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new portfolio for a user",
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


@router.get(
    "/{pid}",
    response_model=Portfolio,
    summary="Retrieve a saved portfolio by its ID",
)
async def read_portfolio(
    pid: str,
    db: Database = Depends(get_db),
) -> Portfolio:
    portfolios_col = db["portfolios"]

    # 1) Fetch by ObjectId
    saved = await portfolios_col.find_one({"_id": ObjectId(pid)})
    if not saved:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found")

    # 2) Convert _id → id
    saved["id"] = str(saved.pop("_id"))

    # 3) Validate into your Pydantic model & return
    return Portfolio.model_validate(saved)


# put
@router.put(
    "/{pid}",
    response_model=Portfolio,
    summary="Update a saved portfolio by its ID"
)
async def update_portfolio(
    body: Portfolio,
    pid: str,
    db: Database = Depends(get_db),
) -> Portfolio:
    portfolios_col = db["portfolios"]

    # 1) Build the update data from the incoming model
    update_data = body.model_dump()

    # 2) Perform find_one_and_update:
    updated = await portfolios_col.find_one_and_update(
        {"_id": ObjectId(pid)},         # filter by the ObjectId
        {"$set": update_data},          # set the new positions
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
    "/{pid}",
    response_model=bool,                       
    summary="Delete a portfolio by its ID",
)
async def delete_portfolio(
    pid: str,
    db: Database = Depends(get_db),            
) -> bool:
    portfolios_col = db["portfolios"]

    # Perform the deletion by ObjectId
    result = await portfolios_col.delete_one(
        {"_id": ObjectId(pid)}
    )

    #  Returns True if exactly one document was removed
    return result.deleted_count == 1
