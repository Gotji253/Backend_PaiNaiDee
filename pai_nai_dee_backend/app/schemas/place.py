from pydantic import BaseModel
from typing import Optional, List

# Forward declaration for Review and Itinerary schemas if they are included here.
# from .review import Review # Example if Review schema is needed
# from .itinerary import Itinerary # Example if Itinerary schema is needed

# Shared properties
class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    # average_rating will likely be calculated or come from DB, not set directly on create/update often

# Properties to receive on creation
class PlaceCreate(PlaceBase):
    pass

# Properties to receive on update
class PlaceUpdate(PlaceBase):
    pass

# Properties shared by models stored in DB
class PlaceInDBBase(PlaceBase):
    id: int
    average_rating: float = 0.0

    class Config:
        from_attributes = True

# Additional properties to return to client
class Place(PlaceInDBBase):
    # reviews: List[Review] = [] # Example: if returning nested reviews
    # itineraries_featuring: List[Itinerary] = [] # Example
    pass

# Properties stored in DB
class PlaceInDB(PlaceInDBBase):
    pass
