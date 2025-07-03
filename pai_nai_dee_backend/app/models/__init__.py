# SQLAlchemy models
# This file makes 'models' a Python package.

from .user import User
from .place import Place, itinerary_place_association
from .review import Review
from .itinerary import Itinerary

# This makes Base available via app.models.Base if needed, though typically Base is imported from db.database
# from app.db.database import Base

__all__ = [
    "User",
    "Place",
    "Review",
    "Itinerary",
    "itinerary_place_association",
    # "Base"
]
