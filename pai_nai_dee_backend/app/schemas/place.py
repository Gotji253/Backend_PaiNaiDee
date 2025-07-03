from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Shared properties
class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None

# Properties to receive on place creation
class PlaceCreate(PlaceBase):
    pass

# Properties to receive on place update
class PlaceUpdate(PlaceBase):
    # All fields are optional for update
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None

# Properties shared by models stored in DB
class PlaceInDBBase(PlaceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # submitter_id: Optional[int] = None # If you add submitter_id to the model

    class Config:
        from_attributes = True # orm_mode = True

# Properties to return to client
class Place(PlaceInDBBase):
    # Potentially add related data here, like average rating or number of reviews
    # avg_rating: Optional[float] = None
    # review_count: Optional[int] = None
    pass

# Properties stored in DB
class PlaceInDB(PlaceInDBBase):
    pass
