from pymongo import AsyncMongoClient # type: ignore
from pymongo.database import Database # type: ignore

from fastapi import FastAPI, APIRouter, Body, Depends, HTTPException, status, Request # type: ignore
import bcrypt

from bson import ObjectId

from .core.db import lifespan
from .api.portfolio import router as portfolio_router
from .api.portfolio import router as user_router
from .api.stock_utils import router as market_router

from .core.dependencies import get_db  # a small helper that returns request.app.mongodb

app = FastAPI(lifespan=lifespan)
app.include_router(portfolio_router)
app.include_router(user_router)
app.include_router(market_router)

from app.auth.auth_handler import sign_jwt
from app.models.user import UserSchema, UserLoginSchema

router = APIRouter(tags=["user"])

@app.get("/")
async def root():
    return {"message": "Hello from main.py"}

@router.post(
    "/user/signup",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and return a JWT"
)
async def create_user(
    user: UserSchema = Body(...),
    db: Database = Depends(get_db),
):
    users_col = db["users"]

    # Check if a user with this email already exists
    exists = await users_col.count_documents(
        {"email": user.email}, limit=1
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with that email already exists."
        )

    # Hash the password (bcrypt wants bytes, so encode it)
    hashed_pw = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")  # decode back to store as a string

    # Build your user document
    user_doc = user.model_dump()
    user_doc["password"] = hashed_pw

    # Insert into MongoDB
    await users_col.insert_one(user_doc)

    # Return a signed JWT for this new user
    return sign_jwt(user.email)

def check_user(data: UserLoginSchema):
    # check is users email in db equals data.email and users password and data.password match. Return true otherwise return false
    pass

@app.post("/user/login", tags=["user"])
async def user_login(
    user: UserLoginSchema = Body(...),  
    db: Database = Depends(get_db)):
    if check_user(user):
        return sign_jwt(user.email)
    return {
        "error": "Wrong login details!"
    }

# TODO: add Cors middleware -> https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
# TODO: considerations for avoiding duplicate portfolios and editing existing portfolios

