import pytest # Still needed for test discovery and asserts
from fastapi.testclient import TestClient
from pai_nai_dee_backend.app.main import app # Import your FastAPI app

# Instantiate the TestClient
client = TestClient(app)

def test_health_check():
    """
    Tests the /health endpoint using TestClient.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root_endpoint():
    """
    Tests the root / endpoint using TestClient.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Pai Nai Dee API"}
