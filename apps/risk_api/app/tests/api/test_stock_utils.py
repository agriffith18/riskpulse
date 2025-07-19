import pytest
import yfinance as yf
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.core.settings import settings
from app.main import app

# run pytest from risk_api directory

@pytest.fixture(scope="module", autouse=True)
def clear_users_collection():
    client = MongoClient(settings.MONGO_URL)
    db = client.get_default_database()
    db["users"].delete_many({})   
    client.close()

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
        
def test_health_check(client):
    resp = client.get("/users/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "mongodb": "connected"}
    
class TestClass:
    def test_get_qoute_success(self, client, monkeypatch):
        class DummyTicker:
           @property
           def info(self):
               return {
                   "currentPrice": 123.45,
                   "previousClose": 120.00,
                   "open": 121.00,
                   "dayHigh": 125.00,
                   "dayLow": 119.00,
               }
                    
        monkeypatch.setattr(yf, "Ticker", lambda symbol: DummyTicker())
        
        response = client.get("market/quote/aapl")
        assert response.status_code == 200, response.json()
        
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["currentPrice"] == 123.45
        assert data["previousClose"] == 120.00
        assert data["open"] == 121.00
        assert data["dayHigh"] == 125.00
        assert data["dayLow"] == 119.00
        