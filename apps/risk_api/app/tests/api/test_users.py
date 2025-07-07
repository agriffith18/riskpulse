import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.core.settings import settings
from app.main import app  

@pytest.fixture(autouse=True)
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
    
def test_create_user(client):
    response = client.post(
        "/users",
        json={
            "first_name": "Arthur",
            "last_name": "Griffith",
            "email_address": "test@gmail.com",
            "password": "123",
            "portfolios": [
                {
                    "positions": [
                        { "symbol": "APPL", "allocation": 0.75 }
                    ]
                }
            ]
        }
    )
    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["first_name"] == "Arthur"
    assert data["last_name"] == "Griffith"
    assert data["email_address"] == "test@gmail.com"
    assert data["portfolios"] == [
            { 
                "positions": [ 
                    { "symbol": "APPL", "allocation": 0.75 } 
                ] 
            }
    ]
    assert isinstance(data["_id"], str)