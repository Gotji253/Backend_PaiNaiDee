import pytest
from fastapi.testclient import TestClient
from pai_nai_dee_backend.app.main import app
from pai_nai_dee_backend.app.core.config import settings

client = TestClient(app)

def test_health_check():
    """
    Tests the /health endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root_endpoint():
    """
    Tests the root / endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": f"Welcome to {settings.PROJECT_NAME}"}

def test_api_v1_root_endpoint():
    """
    Tests the /api/v1/ endpoint.
    """
    response = client.get(f"{settings.API_V1_STR}/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Pai Nai Dee API v1"}
