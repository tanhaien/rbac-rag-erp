from fastapi.testclient import TestClient
from .main import app
from .core.db import db_available


def test_login_and_me():
    client = TestClient(app)

    # Login
    resp = client.post("/auth/login", json={"username": "alice", "password": "secret"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # Me
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["username"] == "alice"


def test_refresh():
    client = TestClient(app)
    login = client.post("/auth/login", json={"username": "bob", "password": "pw"})
    token = login.json()["access_token"]

    r = client.post("/auth/refresh", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    new_token = r.json()["access_token"]
    assert isinstance(new_token, str) and len(new_token) > 20


def test_register_when_db_configured():
    if not db_available():
        # Skip if no DB configured in environment
        return
    client = TestClient(app)
    payload = {"email": "test@example.com", "username": "tester", "password": "pw"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (200, 409)
