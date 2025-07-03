from sqlalchemy import Column, Integer, ForeignKey, Table, DateTime
from sqlalchemy.sql import func
from ..database import Base

# Association table for User <-> Place (Favorites)
user_favorites = Table(
    "user_favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("place_id", Integer, ForeignKey("places.id"), primary_key=True),
    Column("favorited_at", DateTime(timezone=True), server_default=func.now()) # Optional: timestamp when favorited
)

# No Pydantic schema is strictly needed for the association table itself,
# but you might want schemas for requests/responses related to managing favorites,
# e.g., a list of favorited place IDs for a user.

# The relationships themselves will be defined in the User and Place models.
# In User model:
# favorited_places = relationship(
#     "Place",
#     secondary=user_favorites,
#     back_populates="favorited_by_users"
# )

# In Place model:
# favorited_by_users = relationship(
#     "User",
#     secondary=user_favorites,
#     back_populates="favorited_places"
# )
