from fastapi import APIRouter, Depends, HTTPException, status, Path, Body
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services import reviews as reviews_service
from .. import schemas # To access schemas.Review, schemas.ReviewCreate etc.
from ..models.users import User as UserModel
from ..auth import get_current_active_user # Import the real dependency

router = APIRouter(
    tags=["reviews"], # Group endpoints under "reviews" tag in OpenAPI docs
)

@router.post("/api/reviews", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
async def create_new_review(
    review: schemas.ReviewCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Create a new review for a place. Requires authentication.
    """
    if not current_user: # Should be handled by dependency if token is invalid
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # The service function handles checking if place_id in review data is valid.
    db_review = reviews_service.create_review(db=db, review=review, user_id=current_user.id)
    return db_review

@router.get("/api/places/{place_id}/reviews", response_model=List[schemas.Review])
async def read_reviews_for_place(
    place_id: int = Path(..., title="The ID of the place to get reviews for", ge=1),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """
    Get all reviews for a specific place.
    """
    # Optional: Check if place exists first (or let service handle it if it makes sense)
    # db_place = db.query(models.Place).filter(models.Place.id == place_id).first()
    # if not db_place:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    reviews_list = reviews_service.get_reviews_for_place(db=db, place_id=place_id, skip=skip, limit=limit)
    return reviews_list

@router.delete("/api/reviews/{review_id}", response_model=schemas.Review)
async def remove_review(
    review_id: int = Path(..., title="The ID of the review to delete", ge=1),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Delete a review. Only the user who created the review can delete it.
    Requires authentication.
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    deleted_review = reviews_service.delete_review(db=db, review_id=review_id, user_id=current_user.id)
    if not deleted_review: # Service now raises HTTPException, so this might not be strictly needed
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or not authorized to delete")
    return deleted_review
