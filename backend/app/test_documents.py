from fastapi.testclient import TestClient

from .core.db import db_available
from .main import app


def test_documents_endpoints_require_auth():
    """Test that document endpoints require authentication"""
    client = TestClient(app)

    # Test create document without auth
    resp = client.post("/documents/", json={"title": "Test", "content": "Content"})
    assert resp.status_code in [401, 403]  # Either auth required or forbidden

    # Test get document without auth
    resp = client.get("/documents/1")
    assert resp.status_code in [401, 403]  # Either auth required or forbidden

    # Test list documents without auth
    resp = client.get("/documents/")
    assert resp.status_code in [401, 403]  # Either auth required or forbidden


def test_documents_with_valid_auth():
    """Test document endpoints with valid authentication"""
    if not db_available():
        # Skip if no DB configured
        return

    client = TestClient(app)

    # First register and login to get a token
    register_resp = client.post(
        "/auth/register",
        json={"email": "doc@example.com", "username": "docuser", "password": "secret"},
    )
    if register_resp.status_code == 409:
        # User already exists, try login
        pass
    else:
        assert register_resp.status_code == 200

    # Login to get token
    login_resp = client.post(
        "/auth/login", json={"username": "docuser", "password": "secret"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Test create document
    create_resp = client.post(
        "/documents/",
        json={"title": "Test Doc", "content": "Test content"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["id"]

    # Test get document
    get_resp = client.get(
        f"/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Test Doc"

    # Test list documents
    list_resp = client.get("/documents/", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1
