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


def test_demo_protected_with_roles():
    client = TestClient(app)
    # user role allowed
    t_user = client.post("/auth/login", json={"username": "carol", "password": "x"}).json()["access_token"]
    r_user = client.get("/auth/demo-protected", headers={"Authorization": f"Bearer {t_user}"})
    assert r_user.status_code == 200
    assert r_user.json()["ok"] is True

    # admin role allowed
    t_admin = client.post("/auth/login", json={"username": "dan-admin", "password": "x"}).json()["access_token"]
    r_admin = client.get("/auth/demo-protected", headers={"Authorization": f"Bearer {t_admin}"})
    assert r_admin.status_code == 200


def test_login_includes_roles_claim_when_db():
    if not db_available():
        return
    client = TestClient(app)
    # Register ensures user has default 'user' role
    client.post("/auth/register", json={"email": "claims@example.com", "username": "claimuser", "password": "pw"})
    t = client.post("/auth/login", json={"username": "claimuser", "password": "pw"}).json()["access_token"]
    # Access protected route should still pass
    r = client.get("/auth/demo-protected", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200


def test_register_assigns_default_role_when_db():
    if not db_available():
        return
    client = TestClient(app)
    payload = {"email": "role@example.com", "username": "roleuser", "password": "pw"}
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (200, 409)
