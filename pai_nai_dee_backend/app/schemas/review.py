from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Shared properties
class ReviewBase(BaseModel):
    rating: float = Field(..., ge=0.5, le=5.0, description="Rating between 0.5 and 5.0")
    comment: Optional[str] = None

# Properties to receive on creation
class ReviewCreate(ReviewBase):
    place_id: int # User provides this to link review to a place
    # user_id will be taken from current authenticated user, not from payload

# Properties to receive on update
# Usually, reviews are not updated, or only the comment/rating part.
# For simplicity, let's assume only comment can be updated.
class ReviewUpdate(BaseModel):
    rating: Optional[float] = Field(None, ge=0.5, le=5.0, description="Rating between 0.5 and 5.0")
    comment: Optional[str] = None

# Properties shared by models stored in DB
class ReviewInDBBase(ReviewBase):
    id: int
    user_id: int
    place_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Additional properties to return to client
class Review(ReviewInDBBase):
    # To avoid circular imports if User schema includes list of Reviews:
    # user: Optional["User"] = None # If we want to nest user info
    pass

# Schema for a review linked to a user, for User.reviews list perhaps
# class ReviewForUser(ReviewBase):
#     id: int
#     place_id: int # or place_name: str
#     created_at: datetime

# Schema for a review linked to a place, for Place.reviews list
# class ReviewForPlace(ReviewBase):
#     id: int
#     user_id: int # or user_username: str
#     created_at: datetime

# Forward ref solution for User in Review later if needed:
# from .user import User
# Review.model_rebuild()
