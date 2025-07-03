import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool # Ensure single connection for in-memory SQLite

from pai_nai_dee_backend.app.main import app
from pai_nai_dee_backend.app.database import Base, get_db
from pai_nai_dee_backend.app import models # Ensure all models are loaded by Base

# Test Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" # In-memory SQLite for testing

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    poolclass=StaticPool, # Use static pool for in-memory DB with TestClient
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Pytest fixture to create tables for each test function
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine) # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine) # Drop tables after test

client = TestClient(app)

# --- Test Data ---
test_user_data = {
    "email": "testuser@example.com",
    "password": "testpassword",
    "full_name": "Test User"
}
test_admin_data = {
    "email": "admin@example.com",
    "password": "adminpassword",
    "full_name": "Admin User"
}
test_place_data = {
    "name": "Test Cafe",
    "description": "A cozy place for coffee.",
    "address": "123 Test St",
    "latitude": 13.75,
    "longitude": 100.5,
    "category": "cafe",
    "tags": ["coffee", "bakery"]
}

# --- Helper to get admin token ---
def get_admin_auth_header(db_session_for_token):
    # Ensure admin user exists or create one for token generation
    admin_user = db_session_for_token.query(models.User).filter(models.User.email == test_admin_data["email"]).first()
    if not admin_user:
        from pai_nai_dee_backend.app.services.users_service import create_user as create_user_service
        from pai_nai_dee_backend.app.schemas import UserCreate
        admin_schema = UserCreate(**test_admin_data)
        admin_user = create_user_service(db_session_for_token, admin_schema)
        admin_user.is_superuser = True # Make admin
        db_session_for_token.commit()
        db_session_for_token.refresh(admin_user)


    response = client.post("/api/token", data={"username": test_admin_data["email"], "password": test_admin_data["password"]})
    assert response.status_code == 200, f"Failed to get admin token: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- Tests ---

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Pai Nai Dee API"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_user_and_login(db_session: Session):
    # Create user
    response = client.post("/api/users/", json=test_user_data)
    assert response.status_code == 201, response.json()
    user_id = response.json()["id"]
    assert response.json()["email"] == test_user_data["email"]

    # Login with created user
    login_data = {"username": test_user_data["email"], "password": test_user_data["password"]}
    response = client.post("/api/token", data=login_data)
    assert response.status_code == 200, response.json()
    assert "access_token" in response.json()

def test_create_place_as_admin(db_session: Session):
    admin_headers = get_admin_auth_header(db_session)
    response = client.post("/api/places/", json=test_place_data, headers=admin_headers)
    assert response.status_code == 201, response.json()
    assert response.json()["name"] == test_place_data["name"]
    place_id = response.json()["id"]

    # Test get place
    response = client.get(f"/api/places/{place_id}")
    assert response.status_code == 200
    assert response.json()["name"] == test_place_data["name"]

    # Test get all places (check if our new place is in the list)
    response = client.get("/api/places/")
    assert response.status_code == 200
    assert any(p["id"] == place_id for p in response.json())


def test_create_review_for_place(db_session: Session):
    admin_headers = get_admin_auth_header(db_session)
    # 1. Create a place first
    place_response = client.post("/api/places/", json=test_place_data, headers=admin_headers)
    assert place_response.status_code == 201
    place_id = place_response.json()["id"]

    # 2. Create a user to write a review
    user_response = client.post("/api/users/", json=test_user_data)
    assert user_response.status_code == 201
    user_login_data = {"username": test_user_data["email"], "password": test_user_data["password"]}
    token_response = client.post("/api/token", data=user_login_data)
    assert token_response.status_code == 200
    user_token = token_response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Create a review
    review_data = {"place_id": place_id, "rating": 5, "comment": "Loved it!"}
    response = client.post("/api/reviews", json=review_data, headers=user_headers)
    assert response.status_code == 201, response.json()
    assert response.json()["rating"] == 5
    review_id = response.json()["id"]

    # 4. Get reviews for the place
    response = client.get(f"/api/places/{place_id}/reviews")
    assert response.status_code == 200
    reviews_list = response.json()
    assert len(reviews_list) > 0
    assert any(r["id"] == review_id for r in reviews_list)

    # 5. Check average rating update on Place
    place_after_review_response = client.get(f"/api/places/{place_id}")
    assert place_after_review_response.status_code == 200
    place_details = place_after_review_response.json()
    assert place_details["average_rating"] == 5.0
    assert place_details["review_count"] == 1


def test_get_recommendations(db_session: Session):
    # Need a user to get recommendations for
    user_response = client.post("/api/users/", json=test_user_data)
    assert user_response.status_code == 201
    user_login_data = {"username": test_user_data["email"], "password": test_user_data["password"]}
    token_response = client.post("/api/token", data=user_login_data)
    assert token_response.status_code == 200
    user_token = token_response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Create some places (as admin) for recommendations to pick from
    admin_headers = get_admin_auth_header(db_session)
    client.post("/api/places/", json={**test_place_data, "name": "Rec Cafe 1"}, headers=admin_headers)
    client.post("/api/places/", json={**test_place_data, "name": "Rec Cafe 2"}, headers=admin_headers)


    # At this point, recommendations might be based on fallback (e.g. recent places)
    # as the new user has no activity.
    response = client.get("/api/recommendations", headers=user_headers)
    assert response.status_code == 200
    recommendations_data = response.json()
    assert "recommendations" in recommendations_data
    # Further checks would depend on the exact logic of recommendations and user activity logging
    # For now, just check the endpoint is working and returns the structure.
    assert isinstance(recommendations_data["recommendations"], list)

# TODO: Add tests for deletion, updates, edge cases, authorization failures etc.
# TODO: Test user activity logging impact on recommendations (more involved)

# To run tests: pytest
# (Ensure pytest and other dependencies like httpx are installed: pip install pytest httpx)

# Note: The admin user creation within get_admin_auth_header uses the service directly.
# This is okay for test setup but shows a tight coupling that could be refactored
# if more complex test user setups are needed (e.g. using fixtures for users).
# Also, the SECRET_KEY in auth.py should be configurable for tests vs prod.
# For now, tests will use the hardcoded one.
# The in-memory SQLite DB is reset for each test function by the db_session fixture.
