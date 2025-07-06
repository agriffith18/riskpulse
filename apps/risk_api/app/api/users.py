from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from bson import ObjectId
from pymongo.database import Database
from pymongo.collection import ReturnDocument

from app.core.dependencies import get_db
from app.api.schemas import Portfolio, Position

router = APIRouter(prefix="/users", tags=["user"])


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email_address: EmailStr | None = None

    model_config = ConfigDict(extra="ignore")


class UserIn(BaseModel):
    first_name: str
    last_name: str
    email_address: EmailStr
    password: str
    portfolios: List[Portfolio] = []
    
    model_config = ConfigDict(
        schema_extra={
            "example": {
                "first_name": "Arthur",
                "last_name": "Griffith",
                "email_address": "arthur@example.com",
                "password": "p@ssw0rd",
                "portfolios": []
            }
        }
    )

class UserOut(BaseModel):
    id: str | None = Field(None, alias="_id")
    first_name: str
    last_name: str
    email_address: EmailStr
    portfolios: List[Portfolio]

    model_config = ConfigDict(populate_by_name=True, extra="ignore")


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


@router.post(
    "",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create user in database",
)
async def create_user(
    user: UserIn = Body(...),
    db: Database = Depends(get_db),
) -> UserOut:
    users_col = db["users"]

    if await users_col.count_documents({"email_address": user.email_address}, limit=1):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    result = await users_col.insert_one(user.model_dump())
    saved = await users_col.find_one({"_id": result.inserted_id})
    saved["id"] = str(saved.pop("_id"))
    return UserOut.model_validate(saved)


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Return the user with the specified ID",
)
async def get_user(
    user_id: str,
    db: Database = Depends(get_db),
) -> UserOut:
    users_col = db["users"]
    doc = await users_col.find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    doc["id"] = str(doc.pop("_id"))
    return UserOut.model_validate(doc)


@router.put(
    "/{user_id}",
    response_model=UserOut,
    summary="Update the user with the specified ID",
)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: Database = Depends(get_db),
) -> UserOut:
    users_col = db["users"]
    update_data = body.model_dump(exclude_unset=True, by_alias=True)
    updated = await users_col.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    updated["id"] = str(updated.pop("_id"))
    return UserOut.model_validate(updated)


@router.delete(
    "/{user_id}",
    response_model=bool,
    summary="Delete the user with the specified ID",
)
async def delete_user(
    user_id: str,
    db: Database = Depends(get_db),
) -> bool:
    users_col = db["users"]
    result = await users_col.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return True
