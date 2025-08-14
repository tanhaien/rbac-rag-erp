from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json().get("message") == "Welcome to RBAC-RAG for ERP"
