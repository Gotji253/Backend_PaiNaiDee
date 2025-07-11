from sqlalchemy import Column, Integer, String  # Table, ForeignKey removed
from sqlalchemy.orm import relationship

# JSONB import removed as it's unused in this file
# from sqlalchemy.dialects.postgresql import (
#     JSONB,
# )  # For list of strings, if using PostgreSQL

from app.db.database import Base

# Association table for many-to-many relationship between users and interests (if interests are predefined entities)
# For a simple list of strings, a JSONB or similar type might be simpler if not querying interests across users.
# Let's assume interests are strings for now, stored in a JSON-like field or a simple string field if only one.
# If interests are shared/taggable, a separate Interest model and association table would be better.

# For simplicity, let's use a JSONB field for interests if postgres, or a string field for SQLite that we can parse.
# However, SQLAlchemy doesn't have a generic JSON type that works for both SQLite and PostgreSQL out of the box for complex types.
# A common approach for lists of strings is to use a Text field and handle (de)serialization in the application layer,
# or use a JSON type if the DB supports it (JSONB for Postgres, JSON for SQLite >= 3.38.0).
# For now, let's keep it simple. We can refine this later.
# For this example, we'll use a String type and expect comma-separated values, or plan for JSON type.


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # Added email
    hashed_password = Column(String, nullable=False)  # For authentication

    # interests: Column(String) # Example: "food,travel,history" - needs parsing
    # Or using JSON for databases that support it well:
    # interests = Column(JSONB) # For PostgreSQL
    # For broader compatibility without specific JSON types, often handled at schema/service level.
    # Let's omit 'interests' from the direct DB model for now to keep it simple,
    # and it can be added later with a more robust type or relationship.

    # Relationships
    reviews = relationship("Review", back_populates="user")
    itineraries = relationship("Itinerary", back_populates="user")

    # If we implement a "bookmarks" feature:
    # bookmarked_places = relationship("Place", secondary="user_bookmarks_place", back_populates="bookmarked_by_users")
