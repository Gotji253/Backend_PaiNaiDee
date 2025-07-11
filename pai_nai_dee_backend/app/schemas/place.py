from pydantic import BaseModel, constr, PositiveInt, Field
from typing import Optional

# Forward declaration for Review and Itinerary schemas if they are included here.
# from .review import Review # Example if Review schema is needed
# from .itinerary import Itinerary # Example if Itinerary schema is needed


# Shared properties
class PlaceBase(BaseModel):
    name: constr(min_length=1, max_length=100)
    description: Optional[constr(max_length=1000)] = None
    category: Optional[constr(max_length=50)] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    address: Optional[constr(max_length=255)] = None
    # average_rating will likely be calculated or come from DB, not set directly on create/update often


# Properties to receive on creation
class PlaceCreate(PlaceBase):
    pass


# Properties to receive on update
class PlaceUpdate(PlaceBase):
    pass


# Properties shared by models stored in DB
class PlaceInDBBase(PlaceBase):
    id: PositiveInt
    average_rating: float = Field(0.0, ge=0.0, le=5.0)

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
