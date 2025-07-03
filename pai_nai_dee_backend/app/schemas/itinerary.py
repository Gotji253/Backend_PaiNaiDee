from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Forward declaration for Place schema if it's included here for nested responses.
# from .place import Place # Example

# Shared properties
class ItineraryBase(BaseModel):
    name: str
    description: Optional[str] = None

# Properties to receive on creation
class ItineraryCreate(ItineraryBase):
    place_ids: List[int] = [] # List of place IDs to include in this itinerary

# Properties to receive on update
class ItineraryUpdate(ItineraryBase):
    place_ids: Optional[List[int]] = None # Allow updating the list of places

# Properties shared by models stored in DB
class ItineraryInDBBase(ItineraryBase):
    id: int
    user_id: int
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
