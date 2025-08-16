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

    updated_portfolio = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.50},
            {"symbol": "NVDA", "allocation": 0.30},
            {"symbol": "AMZN", "allocation": 0.20},
        ]
    }
    
    response = client.put(f"/portfolio/{portfolio_id}", json=updated_portfolio)
    assert response.status_code == 200, response.json()

    data = response.json()
    assert data["id"] == portfolio_id
    assert data["positions"] == updated_portfolio["positions"]

def test_delete_portfolio(client: TestClient, test_user_id: str):
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

    response = client.delete(f"/portfolio/{portfolio_id}")
    assert response.status_code == 200, response.json()
    assert response.json() == True

    response = client.get(f"/portfolio/id/{portfolio_id}")
    assert response.status_code == 404

def test_get_portfolio_var(client: TestClient, test_user_id: str):
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

    response = client.get(f"/portfolio/{portfolio_id}/var")
    assert response.status_code == 200, response.json()
    var_value = response.json()
    assert isinstance(var_value, float)

def test_get_portfolio_beta(client: TestClient, test_user_id: str):
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

    response = client.get(f"/portfolio/{portfolio_id}/beta")
    assert response.status_code == 200, response.json()
    beta_value = response.json()
    assert isinstance(beta_value, float)

def test_create_portfolio_nonexistent_user(client: TestClient):
    fake_user_id = str(ObjectId())
    portfolio_data = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},
        ]
    }

    response = client.post(
        "/portfolio", 
        json={"user_id": fake_user_id, "portfolio": portfolio_data}
    )
    
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_read_nonexistent_portfolio(client: TestClient):
    fake_portfolio_id = str(ObjectId())
    response = client.get(f"/portfolio/id/{fake_portfolio_id}")
    assert response.status_code == 404
    assert "Portfolio not found" in response.json()["detail"]

def test_update_nonexistent_portfolio(client: TestClient):
    fake_portfolio_id = str(ObjectId())
    portfolio_data = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},
        ]
    }

    response = client.put(f"/portfolio/{fake_portfolio_id}", json=portfolio_data)
    assert response.status_code == 404
    assert "Portfolio not found" in response.json()["detail"]

def test_delete_nonexistent_portfolio(client: TestClient):
    fake_portfolio_id = str(ObjectId())
    response = client.delete(f"/portfolio/{fake_portfolio_id}")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_invalid_portfolio_id_format(client: TestClient):
    invalid_id = "invalid-id"
    response = client.get(f"/portfolio/id/{invalid_id}")
    assert response.status_code == 422

def test_get_var_nonexistent_portfolio(client: TestClient):
    fake_portfolio_id = str(ObjectId())
    response = client.get(f"/portfolio/{fake_portfolio_id}/var")
    assert response.status_code == 404
    assert "Portfolio not found" in response.json()["detail"]

def test_get_beta_nonexistent_portfolio(client: TestClient):
    fake_portfolio_id = str(ObjectId())
    response = client.get(f"/portfolio/{fake_portfolio_id}/beta")
    assert response.status_code == 404
    assert "Portfolio not found" in response.json()["detail"]
