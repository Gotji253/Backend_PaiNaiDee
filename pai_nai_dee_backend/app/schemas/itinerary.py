from pydantic import BaseModel, constr, PositiveInt
from typing import Optional, List
from datetime import datetime

# Forward declaration for Place schema if it's included here for nested responses.
# from .place import Place # Example


# Shared properties
class ItineraryBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    description: Optional[constr(max_length=500)] = None


# Properties to receive on creation
class ItineraryCreate(ItineraryBase):
    place_ids: List[PositiveInt] = []  # List of place IDs to include in this itinerary


# Properties to receive on update
class ItineraryUpdate(ItineraryBase):
    place_ids: Optional[List[PositiveInt]] = None  # Allow updating the list of places


# Properties shared by models stored in DB
class ItineraryInDBBase(ItineraryBase):
    id: PositiveInt
    user_id: PositiveInt
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Additional properties to return to client
class Itinerary(ItineraryInDBBase):
    # places_in_itinerary: List[Place] = [] # Example: if returning nested places
    pass


# Forward ref solution for Place in Itinerary later if needed:
# from .place import Place
# Itinerary.model_rebuild()
