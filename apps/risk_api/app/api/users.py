from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, status # type:ignore
from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr, Field # type:ignore
from bson import ObjectId

# these imports are *used* in class annotations below
from pymongo.database import Database
from pymongo import AsyncMongoClient
from pymongo.collection import ReturnDocument

from ..core.dependencies import get_db 
from ..core.settings import settings


# Single FastAPI instance, with lifespan hook
router = APIRouter(
    title="RiskPulse API",
    lifespan=get_db,
)

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email_address: EmailStr | None = None

    model_config = ConfigDict(extra="ignore")  # allow partial updates


class RiskPulseAPI(FastAPI):
    mongodb_client: AsyncMongoClient
    mongodb: Database

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




@router.get("/health/db", summary="DB health check", tags=["db check"])
async def db_health() -> dict:
    try:
        # this will throw if not connected
        await router.mongodb_client.admin.command("ping")
    except Exception:
        raise HTTPException(status_code=503, detail="MongoDB not reachable")
    return {"status": "ok", "mongodb": "connected"}


@router.post(
    "/create-user", 
    response_model=User, 
    status_code=status.HTTP_201_CREATED, 
    summary="Create user in database", 
    tags=["user"],
)
async def create_user(request: Request, user: User):
    """Insert a new user document and return the saved record"""
    
    user_cols = request.router.mongodb["users"]
    
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


@router.get(
    "/users/{user_id}",
    response_model=User,
    summary="Return the user with the specified ID",
    status_code=status.HTTP_200_OK,
    tags=["user"],
)
async def get_user(
    user_id: str,
    db: Database = Depends(get_db),
) -> User:
    users_col = db["users"]

    # Verify a user with that ObjectId exists
    exists = await users_col.count_documents(
        {"_id": ObjectId(user_id)}, limit=1
    )
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Fetch the full document
    raw = await users_col.find_one({"_id": ObjectId(user_id)})
    # (We know it exists, so raw won't be None)

    # Convert Mongo’s _id → id string
    raw["id"] = str(raw.pop("_id"))

    # Validate & return as a Pydantic model
    return User.model_validate(raw)


@router.put(
    "/users/{user_id}",
    response_model=User,
    summary="Update the user with the specified ID",
    status_code=status.HTTP_200_OK,
    tags=["user"],
)
async def update_user(
    user_id: str,
    body: UserUpdate,                         
    db: Database = Depends(get_db),           
) -> User:
    users_col = db["users"]

    # Check existence by Mongo _id, not some 'user_id' field
    if not await users_col.count_documents(
        {"_id": ObjectId(user_id)}, limit=1
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Extract only the fields the client sent
    update_data = body.model_dump(exclude_unset=True, by_alias=True)

    # atomically update & return *the new* document
    updated = await users_col.find_one_and_update(
        {"_id": ObjectId(user_id)},     
        {"$set": update_data},          
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        # this should be unreachable after the count_documents check,
        # but defensively handle it anyway
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Convert Mongo’s ObjectId to str and alias it to `id`
    updated["id"] = str(updated.pop("_id"))

    # Validate & serialize via your full User model
    return User.model_validate(updated)


@router.delete(
    "/users/{user_id}",
    response_model=bool,
    summary="Delete the user with the specified ID",
    status_code=status.HTTP_200_OK,
    tags=["user"],
)
async def delete_user(
    user_id: str,
    db: Database = Depends(get_db),
) -> bool:
    users_col = db["users"]

    # 404 if missing
    if not await users_col.count_documents({"_id": ObjectId(user_id)}, limit=1):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await users_col.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count == 1
