from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Basic Review schema
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None
    images: Optional[List[str]] = None # List of image URLs

# Schema for creating a new review (place_id will come from path or payload)
class ReviewCreate(ReviewBase):
    place_id: int

# Schema for updating a review (not explicitly in plan, but good practice)
# User should only be able to update their own rating, comment, images
class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = None
    images: Optional[List[str]] = None

# Schema for representing a review in responses
class Review(ReviewBase):
    id: int
    user_id: int
    place_id: int
    created_at: datetime
    updated_at: datetime
    # Could include user details here if needed, e.g., user: UserSchema

    class Config:
        from_attributes = True # For Pydantic V2 (formerly orm_mode)
