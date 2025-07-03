from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Mock data (to be replaced with Firestore integration)
mock_places = [
    {"id": 1, "name": "Wat Arun", "category": "Temple", "rating": 4.8, "reviews": []},
    {"id": 2, "name": "Chatuchak Weekend Market", "category": "Market", "rating": 4.5, "reviews": []},
    {"id": 3, "name": "Grand Palace", "category": "Palace", "rating": 4.7, "reviews": []},
]

mock_itineraries = []
mock_users = []

# --- Pydantic Models ---
class Place(BaseModel):
    id: int
    name: str
    category: str
    rating: float
    reviews: List[str] # Simplified for now

class Review(BaseModel):
    place_id: int
    user_id: int # Assuming user IDs
    rating: float
    comment: Optional[str] = None

class Itinerary(BaseModel):
    id: int
    user_id: int
    name: str
    place_ids: List[int]

class User(BaseModel):
    id: int
    username: str
    interests: List[str] = []

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to Pai Nai Dee API"}

# 1. Search/List Places
@app.get("/places", response_model=List[Place])
async def list_places(category: Optional[str] = None, min_rating: Optional[float] = None):
    """
    List all places, optionally filtered by category or minimum rating.
    """
    results = mock_places
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if min_rating:
        results = [p for p in results if p["rating"] >= min_rating]
    return results

@app.get("/places/{place_id}", response_model=Place)
async def get_place(place_id: int):
    """
    Get details of a specific place.
    """
    for place in mock_places:
        if place["id"] == place_id:
            return place
    raise HTTPException(status_code=404, detail="Place not found")

# 2. Review/Rating System
@app.post("/reviews", response_model=Review)
async def create_review(review: Review):
    """
    Submit a new review for a place.
    (Simplified: adds review text to place, doesn't store review object separately yet)
    """
    for place in mock_places:
        if place["id"] == review.place_id:
            # In a real system, you'd store the full review object
            # and potentially update the place's average rating.
            review_text = f"User {review.user_id} (Rating: {review.rating}): {review.comment or ''}"
            place["reviews"].append(review_text)
            # For now, let's just return the submitted review data
            return review
    raise HTTPException(status_code=404, detail="Place not found for review")

# 3. Itinerary System
@app.post("/itineraries", response_model=Itinerary)
async def create_itinerary(itinerary: Itinerary):
    """
    Create a new itinerary for a user.
    """
    # Simple ID generation for mock data
    new_id = len(mock_itineraries) + 1
    # Create a new dictionary for storage to avoid modifying the input model directly before returning
    itinerary_data = itinerary.model_dump()
    itinerary_data["id"] = new_id
    mock_itineraries.append(itinerary_data)
    # Return the original model but with the ID set, or return the dict if preferred by response_model
    itinerary.id = new_id
    return itinerary

@app.get("/itineraries/user/{user_id}", response_model=List[Itinerary])
async def get_user_itineraries(user_id: int):
    """
    Get all itineraries for a specific user.
    """
    return [it for it in mock_itineraries if it["user_id"] == user_id]

# 4. User/Interests System
@app.post("/users", response_model=User)
async def create_user(user: User):
    """
    Create a new user.
    """
    new_id = len(mock_users) + 1
    user_data = user.model_dump()
    user_data["id"] = new_id
    mock_users.append(user_data)
    user.id = new_id # Set ID on the model instance to be returned
    return user

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Get user details.
    """
    for u in mock_users:
        if u["id"] == user_id:
            return u
    raise HTTPException(status_code=404, detail="User not found")

# 5. Community Feed (Placeholder - to be defined further)
@app.get("/feed")
async def get_community_feed():
    """
    Get the community feed.
    (This is a placeholder and needs more detailed implementation)
    """
    return {"message": "Community feed coming soon!"}

# To run this app (from the backend_painaidee directory):
# uvicorn app.main:app --reload
#
# Example Usage:
# GET http://127.0.0.1:8000/places
# GET http://127.0.0.1:8000/places?category=Temple
# POST http://127.0.0.1:8000/reviews (with JSON body for Review model)
# POST http://127.0.0.1:8000/itineraries (with JSON body for Itinerary model)
# ... and so on.
