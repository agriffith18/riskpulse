from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, status # type:ignore
from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr, Field # type:ignore
from bson import ObjectId

# these imports are *used* in class annotations below
from pymongo import AsyncMongoClient
from pymongo.database import Database

from ..core.dependencies import get_db 
from ..core.settings import settings

router = APIRouter()

class RiskPulseAPI(FastAPI):
    mongodb_client: AsyncMongoClient
    mongodb: Database

# Single FastAPI instance, with lifespan hook
router = RiskPulseAPI(
    title="RiskPulse API",
    lifespan=get_db,
)


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
    summary="Create user in database", tags=["user"],
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