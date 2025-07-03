# This file makes 'models' a Python package.

# Import all your models here to make them easily accessible
# when SQLAlchemy Base.metadata.create_all(engine) is called,
# or when Alembic generates migrations.

from .user import User
from .place import Place, itinerary_place_association
from .review import Review
from .itinerary import Itinerary

# You can also define __all__ if you want to control what 'from app.models import *' imports
__all__ = ["User", "Place", "Review", "Itinerary", "itinerary_place_association"]
