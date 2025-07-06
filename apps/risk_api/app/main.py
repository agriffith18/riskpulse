from fastapi import FastAPI, APIRouter, Body, Depends, HTTPException, status
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId
import bcrypt

from .core.db import RiskPulseAPI, lifespan
from .core.dependencies import get_db
from .api.portfolio import router as portfolio_router
from .api.stock_utils import router as market_router
from app.auth.auth_handler import sign_jwt
from app.models.user import UserSchema, UserLoginSchema

# Use FastAPI subclass so .mongodb and .mongodb_client exist
app = RiskPulseAPI(lifespan=lifespan)

@app.get("/", summary="Root health check")
async def root():
    return {"message": "Hello from main.py"}

# Mount existing routers
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
app.include_router(market_router, prefix="/market", tags=["market"])

user_router = APIRouter(prefix="/user", tags=["user"])

@user_router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and return a JWT",
)
async def create_user(
    user: UserSchema = Body(...),
    db: Database = Depends(get_db),
):
    users_col: Collection = db["users"]

    if await users_col.count_documents({"email": user.email}, limit=1):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists."
        )

    hashed_pw = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    user_doc = user.model_dump()
    user_doc["password"] = hashed_pw
    await users_col.insert_one(user_doc)

    return sign_jwt(user.email)


@user_router.post(
    "/login",
    summary="Authenticate user and return JWT",
)
async def user_login(
    creds: UserLoginSchema = Body(...),
    db: Database = Depends(get_db),
):
    users_col: Collection = db["users"]

    user_doc = await users_col.find_one({"email": creds.email})
    if not user_doc or not bcrypt.checkpw(
        creds.password.encode("utf-8"),
        user_doc["password"].encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong login details"
        )

    return sign_jwt(creds.email)

app.include_router(user_router)
