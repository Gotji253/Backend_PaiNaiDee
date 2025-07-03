from fastapi.testclient import TestClient
# Adjust the import path according to your project structure
# This assumes your main.py is in an 'app' directory and 'app' is in PYTHONPATH
# If backend_painaidee is the root for running pytest, this should work.
from backend_painaidee.app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Pai Nai Dee API"}

def test_list_places_no_filter():
    response = client.get("/places")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Assuming mock_places is not empty
    assert data[0]["name"] == "Wat Arun"

def test_list_places_filter_category():
    response = client.get("/places?category=Temple")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for place in data:
        assert place["category"].lower() == "temple"

def test_list_places_filter_min_rating():
    response = client.get("/places?min_rating=4.6")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for place in data:
        assert place["rating"] >= 4.6

def test_get_place_exists():
    response = client.get("/places/1") # Assuming Wat Arun has id 1
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Wat Arun"
    assert data["id"] == 1

def test_get_place_not_exists():
    response = client.get("/places/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Place not found"}

def test_create_review_for_existing_place():
    review_data = {
        "place_id": 1,
        "user_id": 101,
        "rating": 5.0,
        "comment": "Amazing!"
    }
    response = client.post("/reviews", json=review_data)
    assert response.status_code == 200
    data = response.json()
    assert data["place_id"] == review_data["place_id"]
    assert data["user_id"] == review_data["user_id"]
    assert data["rating"] == review_data["rating"]
    assert data["comment"] == review_data["comment"]

    # Check if the review was "added" to the mock place (simplified check)
    place_response = client.get("/places/1")
    place_data = place_response.json()
    expected_review_text = f"User {review_data['user_id']} (Rating: {review_data['rating']}): {review_data['comment']}"
    assert expected_review_text in place_data["reviews"]

def test_create_review_for_non_existing_place():
    review_data = {
        "place_id": 999,
        "user_id": 102,
        "rating": 4.0,
        "comment": "Good"
    }
    response = client.post("/reviews", json=review_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Place not found for review"}

def test_create_and_get_user():
    user_data = {"id": 0, "username": "testuser", "interests": ["temples", "food"]} # id will be overwritten
    response_create = client.post("/users", json=user_data)
    assert response_create.status_code == 200
    created_user = response_create.json()
    assert created_user["username"] == user_data["username"]
    assert created_user["interests"] == user_data["interests"]
    assert "id" in created_user and isinstance(created_user["id"], int)

    user_id = created_user["id"]
    response_get = client.get(f"/users/{user_id}")
    assert response_get.status_code == 200
    fetched_user = response_get.json()
    assert fetched_user == created_user

def test_get_non_existing_user():
    response = client.get("/users/9999")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}

def test_create_and_get_itinerary():
    # First, ensure a user exists or create one for the itinerary
    # For simplicity, we'll assume user ID 1 might exist from previous tests or mock data
    # Or, we could create one:
    client.post("/users", json={"id":0, "username": "itinerary_user"})


    itinerary_data = {
        "id": 0, # Will be overwritten
        "user_id": 1, # Assuming user 1 exists or is created
        "name": "My Bangkok Trip",
        "place_ids": [1, 3] # Wat Arun, Grand Palace
    }
    response_create = client.post("/itineraries", json=itinerary_data)
    assert response_create.status_code == 200
    created_itinerary = response_create.json()
    assert created_itinerary["user_id"] == itinerary_data["user_id"]
    assert created_itinerary["name"] == itinerary_data["name"]
    assert created_itinerary["place_ids"] == itinerary_data["place_ids"]
    assert "id" in created_itinerary and isinstance(created_itinerary["id"], int)

    itinerary_id = created_itinerary["id"]
    # Test get itineraries for user
    response_get_user_itineraries = client.get(f"/itineraries/user/{itinerary_data['user_id']}")
    assert response_get_user_itineraries.status_code == 200
    user_itineraries = response_get_user_itineraries.json()
    assert isinstance(user_itineraries, list)
    # Check if the created itinerary is in the list
    found = False
    for it in user_itineraries:
        if it["id"] == itinerary_id:
            assert it["name"] == itinerary_data["name"]
            found = True
            break
    assert found, "Created itinerary not found in user's list"

def test_get_community_feed():
    response = client.get("/feed")
    assert response.status_code == 200
    assert response.json() == {"message": "Community feed coming soon!"}
