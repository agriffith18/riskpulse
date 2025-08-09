import pytest
from bson import ObjectId
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

@pytest.fixture()  # function scoped by default
def test_user_id():
    # Create a throwaway user for each test; delete after the test.
    client_db = MongoClient(settings.MONGO_URL)
    db = client_db.get_default_database()
    user_id = str(db["users"].insert_one({"name": "Test User"}).inserted_id)

    # hand the user_id to the test
    try:
        yield user_id
    finally:
        # tear down phase: when test completes we remove the user and close the connection
        db["users"].delete_one({"_id": ObjectId(user_id)})
        client_db.close()

def test_health_check(client):
    response = client.get("/portfolio/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mongodb": "connected"}


def test_create_and_read_portfolio(client: TestClient, test_user_id: str):
    portfolio_data = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},
        ]
    }

    response = client.post(
        "/portfolio", 
        json={"user_id": test_user_id, "portfolio": portfolio_data}
    )
    
    assert response.status_code == 201, response.json()
    portfolio_id = response.json()
    assert isinstance(portfolio_id, str)

    response = client.get(f"/portfolio/id/{portfolio_id}")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["id"] == portfolio_id
    assert data["positions"] == portfolio_data["positions"]

def test_update_portfolio(client: TestClient, test_user_id: str):
    original_portfolio = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},
        ]
    }
    
    response = client.post(
        "/portfolio", 
        json={"user_id": test_user_id, "portfolio": original_portfolio}
    )
    
    assert response.status_code == 201, response.json()
    portfolio_id = response.json()

    updated = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.50},
            {"symbol": "NVDA", "allocation": 0.30},
            {"symbol": "AMZN", "allocation": 0.20},
        ]
    }
    
    response = client.put(f"/portfolio/{portfolio_id}", json=updated)
    assert response.status_code == 200, response.json()

    data = response.json()
    assert data["id"] == portfolio_id
    assert data["positions"] == updated["positions"]
