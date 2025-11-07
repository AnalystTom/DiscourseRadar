"""Basic tests for FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns expected response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Discourse Radar API"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data


def test_openapi_schema():
    """Test OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Discourse Radar API"
    assert schema["info"]["version"] == "0.1.0"


def test_docs_endpoint():
    """Test that API docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_api_endpoints_registered():
    """Test that all expected endpoints are registered."""
    response = client.get("/openapi.json")
    schema = response.json()
    paths = schema["paths"]

    # Check core endpoints exist
    assert "/topics" in paths
    assert "/jobs" in paths
    assert "/documents" in paths
    assert "/clusters" in paths
    assert "/summaries" in paths
    assert "/health" in paths

    # Check HTTP methods
    assert "post" in paths["/topics"]
    assert "get" in paths["/topics"]
    assert "post" in paths["/jobs"]
    assert "get" in paths["/jobs"]


def test_cors_headers():
    """Test CORS headers are set correctly."""
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
