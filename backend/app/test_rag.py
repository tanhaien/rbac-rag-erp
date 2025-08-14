"""
Tests for RAG pipeline functionality.
"""

import pytest
from fastapi.testclient import TestClient

from .auth.models import User
from .auth.service import auth_service
from .main import app


@pytest.fixture
def test_user():
    """Create a test user."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        is_active=True,
    )


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers."""
    token = auth_service.create_access_token(test_user.email)
    return {"Authorization": f"Bearer {token}"}


def test_rag_query(auth_headers):
    """Test RAG query endpoint."""
    client = TestClient(app)
    response = client.post(
        "/rag/query",
        headers=auth_headers,
        json={
            "query": "What is the main topic?",
            "user_id": 1,
            "max_results": 5,
            "similarity_threshold": 0.7,
        },
    )

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "answer" in data
    assert "sources" in data
    assert "processing_time" in data


def test_rag_stats(auth_headers):
    """Test RAG stats endpoint."""
    client = TestClient(app)
    response = client.get("/rag/stats", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_chunks" in data
    assert "vector_store_type" in data
    assert "embedding_service" in data


def test_rag_query_unauthorized():
    """Test RAG query without authentication."""
    client = TestClient(app)
    response = client.post(
        "/rag/query",
        json={"query": "What is the main topic?", "user_id": 1, "max_results": 5},
    )

    assert response.status_code in [
        401,
        403,
    ]  # Both are acceptable for unauthorized access
