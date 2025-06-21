from pymongo import AsyncMongoClient
from pymongo.database import Database

from fastapi import FastAPI, Body # type: ignore
from .core.db import lifespan
from .api.portfolio import router as portfolio_router
from .api.portfolio import router as user_router
from .api.stock_utils import router as market_router

app = FastAPI(lifespan=lifespan)
app.include_router(portfolio_router)
app.include_router(user_router)
app.include_router(market_router)

from app.auth.auth_handler import sign_jwt
from app.models.user import UserSchema, UserLoginSchema

@app.get("/")
async def root():
    return {"message": "Hello from main.py"}

@app.post("/user/signup", tags=["user"])
async def create_user(user: UserSchema = Body(...)):
    # replace with db call, making sure to hash the password first
    return sign_jwt(user.email)

def check_user(data: UserLoginSchema):
    # check is users email in db equals data.email and users password and data.password match. Return true otherwise return false
    pass

@app.post("/user/login", tags=["user"])
async def user_login(user: UserLoginSchema = Body(...)):
    if check_user(user):
        return sign_jwt(user.email)
    return {
        "error": "Wrong login details!"
    }

# TODO: add Cors middleware -> https://fastapi.tiangolo.com/tutorial/cors/#use-corsmiddleware
# TODO: considerations for avoiding duplicate portfolios and editing existing portfolios

