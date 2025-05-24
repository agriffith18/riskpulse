# db.py  –  initialise and tear‑down a typed async MongoDB client and database
from fastapi import FastAPI # type: ignore
from pymongo import AsyncMongoClient
from pymongo.database import Database
from contextlib import asynccontextmanager
from .settings import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ────────────────────────────────────────────────────

    # 1) Create the AsyncMongoClient and annotate the local variable
    client: AsyncMongoClient = AsyncMongoClient(
        settings.MONGO_URL,
        serverSelectionTimeoutMS=5000,
    )
    # 2) Attach it to the FastAPI app (no annotation here)
    app.mongodb_client = client

    # 3) Fail fast if credentials/URI are bad
    await client.admin.command("ping")

    # 4) Create the Database handle and annotate the local variable
    db: Database = client.get_default_database()
    # 5) Attach it to the FastAPI app (no annotation here)
    app.mongodb = db

    print("✅ MongoDB connected.")

    # Hand control back—routes can now run
    yield

    # ── SHUTDOWN ──────────────────────────────────────────────────
    # Close the client and release resources
    await client.close()
    print("🛑 MongoDB disconnected.")