from pydantic import BaseModel, conint
from typing import Optional
from datetime import datetime

from .user import User as UserSchema # For embedding user info in review response
from .place import PlaceBase as PlaceSchema # For embedding place info (optional)


# Shared properties
class ReviewBase(BaseModel):
    rating: conint(ge=1, le=5) # Rating between 1 and 5
    comment: Optional[str] = None

# Properties to receive on review creation
class ReviewCreate(ReviewBase):
    place_id: int # Must specify which place the review is for
    # user_id will be taken from the authenticated user

# Properties to receive on review update
class ReviewUpdate(ReviewBase):
    rating: Optional[conint(ge=1, le=5)] = None # All fields optional for update
    comment: Optional[str] = None

# Properties shared by models stored in DB
class ReviewInDBBase(ReviewBase):
    id: int
    user_id: int
    place_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True # orm_mode = True

# Properties to return to client
class Review(ReviewInDBBase):
    # Optionally include related data, like user's name or place name
    user: Optional[UserSchema] = None # Embed user information
    # place: Optional[PlaceSchema] = None # Embed place information if needed

# For cases where you only want to return the review with basic user info (like ID and email)
class ReviewWithUserInfo(ReviewInDBBase):
    user: UserSchema # Example, customize as needed

# Properties stored in DB
class ReviewInDB(ReviewInDBBase):
    pass
