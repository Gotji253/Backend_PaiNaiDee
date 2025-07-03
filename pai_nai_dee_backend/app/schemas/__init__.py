# Pydantic schemas
# This file makes 'schemas' a Python package.

from .user import User, UserCreate, UserUpdate, UserInDB
from .place import Place, PlaceCreate, PlaceUpdate, PlaceInDB
from .review import Review, ReviewCreate, ReviewUpdate # Removed ReviewInDB
from .itinerary import Itinerary, ItineraryCreate, ItineraryUpdate # Removed ItineraryInDB

# Token schemas for authentication
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

__all__ = [
    "User", "UserCreate", "UserUpdate", "UserInDB",
    "Place", "PlaceCreate", "PlaceUpdate", "PlaceInDB",
    "Review", "ReviewCreate", "ReviewUpdate", # Removed ReviewInDB
    "Itinerary", "ItineraryCreate", "ItineraryUpdate", # Removed ItineraryInDB
    "Token", "TokenData",
]
