from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.database import Base
from .place import itinerary_place_association  # Import the association table


class Itinerary(Base):
    __tablename__ = "itineraries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # User who owns the itinerary

    # Relationships
    user = relationship("User", back_populates="itineraries")

    # Many-to-many relationship with Place
    places_in_itinerary = relationship(
        "Place",
        secondary=itinerary_place_association,
        back_populates="itineraries_featuring",  # This back_populates needs to be defined in Place model
    )


# Now, I need to go back and add the `itineraries_featuring` back_populates in `place.py`
# The `Place` model currently has:
# itineraries_featuring = relationship("Itinerary", secondary=itinerary_place_association, back_populates="places_in_itinerary")
# This seems correct. I'll double check.

# In Place model:
# itineraries_featuring = relationship("Itinerary", secondary=itinerary_place_association, back_populates="places_in_itinerary")
# In Itinerary model:
# places_in_itinerary = relationship("Place", secondary=itinerary_place_association, back_populates="itineraries_featuring")
# This circular dependency for back_populates is standard for many-to-many.

# Let's ensure the back_populates in Place.py is correctly named.
# Reading Place model again to confirm `itineraries_featuring`
# The current `place.py` has:
# # itineraries_featuring = relationship("Itinerary", secondary=itinerary_place_association, back_populates="places_in_itinerary")
# This line is commented out. I need to uncomment it and ensure it's correctly defined.

# Okay, the `itinerary_place_association` table is defined in `place.py`.
# The relationship in `Itinerary` uses `back_populates="itineraries_featuring"`.
# So, `Place` model should have `itineraries_featuring = relationship(...) back_populates="places_in_itinerary"`.
# I'll need to modify `place.py` to correctly define this relationship.
