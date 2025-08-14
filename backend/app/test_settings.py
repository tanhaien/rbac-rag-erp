from fastapi.testclient import TestClient

from .main import app


def test_health_default_env():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "env" in data and "debug" in data
    assert "cerbos" in data and isinstance(data["cerbos"], dict)
