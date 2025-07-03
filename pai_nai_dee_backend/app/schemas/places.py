from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []

class PlaceCreate(PlaceBase):
    pass

class PlaceUpdate(PlaceBase):
    name: Optional[str] = None # Allow partial updates

class PlaceInDBBase(PlaceBase):
    id: int
    created_at: datetime
    updated_at: datetime
    average_rating: float = 0.0
    review_count: int = 0

    class Config:
        from_attributes = True

# Schema for responses, could include more details like reviews if needed
class Place(PlaceInDBBase):
    pass

# Schema for place recommendations (could be simpler than full Place schema)
class PlaceRecommendation(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    # Add other fields relevant for a recommendation card, e.g., main image, short description

    class Config:
        from_attributes = True
