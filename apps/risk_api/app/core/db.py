from fastapi import FastAPI # type: ignore
from pymongo import AsyncMongoClient
from contextlib import asynccontextmanager
from .settings import settings  # type: ignore

@asynccontextmanager                     # Turns this coroutine into a context manager
async def lifespan(app: FastAPI):        # Receives the FastAPI instance at startup
    # ────── 1. STARTUP CODE ──────
    # Create one shared, non-blocking MongoDB client with a 5-second “can’t connect” timeout.
    app.mongodb_client = AsyncMongoClient(
        settings.MONGO_URL, serverSelectionTimeoutMS=5000
    )

    # Immediately verify that the cluster is reachable; raises if not.
    await app.mongodb_client.admin.command("ping")

    # Convenience alias: default database object (based on URI’s path).
    app.mongodb = app.mongodb_client.get_default_database()

    # Log a friendly confirmation so you know the DB connection succeeded.
    print("✅ MongoDB connected.")

    # Yield control back to FastAPI; the application now starts serving requests.
    yield

    # ────── 2. SHUTDOWN CODE ──────
    # Close the client gracefully, releasing sockets and event-loop resources.
    await app.mongodb_client.close()

    # Log that the connection pool is gone.
    print("🛑 MongoDB disconnected.")
    