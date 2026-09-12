import os
os.environ["DATABASE_URL"] = "sqlite:///./test_helpdesk.db"
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
client = TestClient(app)


def auth():
    response = client.post("/api/auth/register", json={"email": "test@example.com", "password": "secret123", "name": "Tester"})
    if response.status_code != 200:
        response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "secret123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_register_and_me():
    headers = auth()
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "test@example.com"


def test_chat_and_ticket_creation():
    headers = auth()
    response = client.post("/api/chat", headers=headers, json={"message": "WiFi is not working, create a ticket"})
    body = response.json()
    assert body["intent"] == "network"
    assert body["ticket_id"].startswith("HD-")
    assert client.get("/api/tickets", headers=headers).json()[0]["status"] == "OPEN"