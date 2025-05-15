from fastapi import FastAPI # type: ignore
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from .settings import settings  # type: ignore

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Called once, at startup
    app.mongodb_client = AsyncIOMotorClient(
        settings.MONGO_URL, serverSelectionTimeoutMS=5000
    )
    # verify right away
    await app.mongodb_client.admin.command("ping")
    app.mongodb = app.mongodb_client.get_default_database()
    print("✅ MongoDB connected.")
    yield
    # Called once, at shutdown
    app.mongodb_client.close()
    print("🛑 MongoDB disconnected.")
