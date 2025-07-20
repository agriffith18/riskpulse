import pytest
import yfinance as yf
import pandas as pd 
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.core.settings import settings
from app.main import app

# run pytest from app directory

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
    portfolios = {
        "positions": [
            {"symbol": "AAPL", "allocation": 0.75},
            {"symbol": "NVDA", "allocation": 0.25},    
        ]
    }
    
    def test_get_quote_success(self, client: TestClient, monkeypatch):
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
    
    
    def test_calculate_historical_1day_var(self, client: TestClient):
        response = client.post("/market/var", json={
            "portfolio": self.portfolios, 
            "confidence_level": 0.95,
            "start_date": "2020-01-01",
            "end_date": None,
        })

        assert response.status_code == 200, response.json()
        data = response.json()

        # just check that it's a float and positive because VaR represents the magnitude of a loss
        assert isinstance(data, float)
        assert data > 0

    def test_calculate_daily_returns(self, client: TestClient, monkeypatch):
        
        def mock_download(*args, **kwargs):
            return pd.DataFrame({
                ("Close", "AAPL"): [100, 110, 105],
                ("Close", "NVDA"): [200, 202, 204]
            }, index=pd.date_range("2020-01-01", periods=3))
            
        monkeypatch.setattr(yf, "download", mock_download) 
            
        response = client.post("/market/daily-returns", json={
            "portfolio": self.portfolios,
            "start_date": "2020-01-01",
            "end_date": None,
        })
        
        assert response.status_code == 200, response.json()
        data = response.json()
        assert isinstance(data, float)
        
        expected_returns = pd.Series([0.0775, -0.031625])
        expected_std = expected_returns.std()
        