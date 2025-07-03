from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .place import Place # Import Place schema for responses

# Schema for returning a list of favorited places for a user
class UserFavoritePlaces(BaseModel):
    user_id: int
    favorite_places: List[Place] # List of full Place details

    class Config:
        from_attributes = True

# Schema for the data in the association table (if needed directly)
class FavoriteRecord(BaseModel):
    user_id: int
    place_id: int
    favorited_at: datetime

    class Config:
        from_attributes = True

# Response for adding/removing a favorite
class FavoriteResponse(BaseModel):
    message: str
    user_id: int
    place_id: int
    is_favorited: bool # True if added, False if removed
