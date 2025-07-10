from .user import User
from .place import Place
from .trip import Trip, trip_place_association
from .review import Review

# This line is important for Alembic or similar tools to find the models
# when auto-generating migrations, and for creating tables.
from app.db.base import Base
