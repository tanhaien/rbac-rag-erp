from fastapi.testclient import TestClient
from .main import app


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
