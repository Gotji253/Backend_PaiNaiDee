from pydantic import BaseModel, ConfigDict, conint
from typing import Optional
from datetime import datetime


# Shared properties
class ReviewBase(BaseModel):
    rating: conint(ge=1, le=5)  # Rating must be between 1 and 5
    comment: Optional[str] = None


# Properties to receive on item creation
class ReviewCreate(ReviewBase):
    place_id: int  # Must be provided on creation
    # owner_id will be derived from the authenticated user


# Properties to receive on item update
class ReviewUpdate(ReviewBase):
    rating: Optional[conint(ge=1, le=5)] = None  # All fields optional for update
    comment: Optional[str] = None
    # place_id and owner_id are generally not updatable for a review


# Properties shared by models stored in DB
class ReviewInDBBase(ReviewBase):
    id: int
    place_id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Review(ReviewInDBBase):
    # Optionally, could include nested owner (User) or place (Place) info here
    # For now, keeping it simple with IDs.
    pass


# Properties stored in DB (if different)
class ReviewInDB(ReviewInDBBase):
    pass
