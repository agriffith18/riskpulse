import pytest
from fastapi.testclient import TestClient
from pymongo import MongoClient
from app.core.settings import settings
from app.main import app  

@pytest.fixture(scope="module", autouse=True)
def clear_users_collection():
    client = MongoClient(settings.MONGO_URL)
    db = client.get_default_database()
    db["users"].delete_many({})   
    client.close()

@pytest.fixture(scope="module") # scope=module -> only invoked once per test module (the default is to invoke once per test function)
def client():
    with TestClient(app) as c: # entering the with block it starts a ASGI server and runs FASTAPI startup events like connecting to Mongo.
        yield c # leaving with block automatically call context-manager __exit__ method, shutting down server.

def test_health_check(client):
    resp = client.get("/users/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "mongodb": "connected"}
 
class TestClass:  
    created_id: str = ""
     
    def test_create_user(self, client):
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
               {"positions": [{"symbol": "APPL", "allocation": 0.75}]}
        ]
        
        assert isinstance(data["_id"], str)
        TestClass.created_id = data["_id"]
        
    def test_get_user(self, client):
        assert TestClass.created_id, "test_create_user must run first"
        
        response = client.get(f"/users/{TestClass.created_id}")
        assert response.status_code == 200, response.json()
        
        data = response.json()
        assert data["_id"] == TestClass.created_id
        assert data["first_name"] == "Arthur"
        assert data["last_name"] == "Griffith"
        assert data["email_address"] == "test@gmail.com"
        assert data["portfolios"] == [
            {"positions": [{"symbol": "APPL", "allocation": 0.75}]}
        ]