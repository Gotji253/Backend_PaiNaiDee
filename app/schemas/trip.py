from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date # For date fields

from .place import Place # To show nested Place information

# Shared properties
class TripBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

# Properties to receive on item creation
class TripCreate(TripBase):
    owner_id: int # Must be provided on creation
    place_ids: Optional[List[int]] = [] # List of Place IDs to associate with the trip

# Properties to receive on item update
class TripUpdate(TripBase):
    name: Optional[str] = None # All fields optional for update
    owner_id: Optional[int] = None # Potentially allow changing owner (admin?)
    place_ids: Optional[List[int]] = None # Allow updating associated places

# Properties shared by models stored in DB
class TripInDBBase(TripBase):
    id: int
    owner_id: int
    # For ORM mode, to allow direct mapping from SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)

# Properties to return to client
class Trip(TripInDBBase):
    places: List[Place] = [] # Return full Place objects associated with the trip

# Properties stored in DB (if different from Trip, e.g. if places were just IDs)
class TripInDB(TripInDBBase):
    # If places were stored as a list of IDs in some NoSQL scenario, it might go here.
    # For SQLAlchemy with relationships, TripInDBBase and Trip usually suffice,
    # as the relationship loading is handled by SQLAlchemy and Pydantic's ORM mode.
    pass
