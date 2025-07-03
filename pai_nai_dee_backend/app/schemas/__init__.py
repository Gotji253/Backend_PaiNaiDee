# This file makes 'schemas' a Python package.

# Import all your schemas here for easier access, e.g., from app.schemas import User, Place
from .user import User, UserCreate, UserUpdate, UserInDBBase, UserInDB
from .place import Place, PlaceCreate, PlaceUpdate, PlaceInDBBase, PlaceInDB
from .review import Review, ReviewCreate, ReviewUpdate, ReviewInDBBase
from .itinerary import Itinerary, ItineraryCreate, ItineraryUpdate, ItineraryInDBBase
from .token import Token, TokenData  # Correctly import from token.py

# You can also define __all__ to specify what 'from app.schemas import *' imports
__all__ = [
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDBBase",
    "UserInDB",
    "Place",
    "PlaceCreate",
    "PlaceUpdate",
    "PlaceInDBBase",
    "PlaceInDB",
    "Review",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewInDBBase",
    "Itinerary",
    "ItineraryCreate",
    "ItineraryUpdate",
    "ItineraryInDBBase",
    "Token",
    "TokenData",
]
