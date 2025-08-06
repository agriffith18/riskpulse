import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.core.settings import settings
from app.main import app

# run pytest from app directory

@pytest.fixture(scope="module", autouse=True)
def clear_portfolio_collection():
    client = MongoClient(settings.MONGO_URL)
    db = client.get_default_database()
    db["portfolios"].delete_many({})   
    client.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
        
def test_health_check(client):
    resp = client.get("/portfolio/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "mongodb": "connected"}


def test_create_and_read_portfolio(client: TestClient):
    # Step 1: Insert test user
    client_db = MongoClient(settings.MONGO_URL)
    db = client_db.get_default_database()
    user_id = str(db["users"].insert_one({"name": "Test User"}).inserted_id)
    client_db.close()

    portfolio_data = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},
        ]
    }

    # Step 2: Create portfolio
    response = client.post(
        "/portfolio",
        json={"user_id": user_id, "portfolio": portfolio_data}
    )
    assert response.status_code == 201, response.json()
    portfolio_id = response.json()
    assert isinstance(portfolio_id, str)

    # Step 3: Read portfolio
    response = client.get(f"/portfolio/id/{portfolio_id}")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["id"] == portfolio_id
    assert data["positions"] == portfolio_data["positions"]
    