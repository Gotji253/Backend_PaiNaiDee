from pydantic import BaseModel, ConfigDict
from typing import Optional


# Shared properties
class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None


# Properties to receive on item creation
class PlaceCreate(PlaceBase):
    pass


# Properties to receive on item update
class PlaceUpdate(PlaceBase):
    name: Optional[str] = None  # All fields are optional for update


# Properties shared by models stored in DB
class PlaceInDBBase(PlaceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Place(PlaceInDBBase):
    pass


# Properties stored in DB
class PlaceInDB(PlaceInDBBase):
    pass
