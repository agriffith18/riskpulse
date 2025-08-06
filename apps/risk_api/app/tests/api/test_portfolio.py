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


"""
class CreatePortfolioRequest(BaseModel):
    user_id: str
    portfolio: Portfolio
"""
class TestClass:
    portfolio = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},    
        ]
    }
    
    def test_create_portfolio(self, client: TestClient):
        client_db = MongoClient(settings.MONGO_URL)
        db = client_db.get_default_database()
        user_id = str(db["users"].insert_one({ "name": "Test User" }).inserted_id)
        client_db.close()
        
        response = client.post(
            "/portfolio",
            json={
                "user_id": user_id,
                "portfolio": self.portfolio
            }
        )
        
        assert response.status_code == 201, response.json()
        data = response.json()
        assert isinstance(data, str)
        TestClass.created_id = data
        