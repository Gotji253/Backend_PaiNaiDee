from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud # Adjusted import
from .. import models # Adjusted import
from .. import schemas # Adjusted import
from ..database import get_db # Adjusted import
from ..auth.dependencies import get_current_active_user # For protected routes

router = APIRouter()

# Endpoint to create a review for a specific place
# This could also be POST /api/reviews with place_id in the body
@router.post("/places/{place_id}/reviews", response_model=schemas.review.Review, status_code=status.HTTP_201_CREATED)
def create_review_for_place(
    place_id: int, # Taken from path
    review_in: schemas.review.ReviewCreate, # Review data from body
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    # Check if place exists
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Place with id {place_id} not found")

    # Ensure review_in.place_id matches the path if it's part of ReviewCreate schema
    # Or, if ReviewCreate does not include place_id, set it here.
    # For this example, ReviewCreate expects place_id. Let's ensure they match or just use place_id from path.
    if review_in.place_id != place_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Place ID in path and body do not match.")

    # Check if this user has already reviewed this place (optional, based on product requirements)
    # existing_review = db.query(models.review.Review).filter(
    #     models.review.Review.place_id == place_id,
    #     models.review.Review.user_id == current_user.id
    # ).first()
    # if existing_review:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this place.")

    new_review = crud.review.create_review(db=db, review=review_in, user_id=current_user.id)
    # Eagerly load user data for the response if schema expects it
    # This can be done via relationship loading options in SQLAlchemy query or by manually setting it
    # For simplicity, if your Review schema expects a User schema, ensure the ORM model has it loaded.
    # db.refresh(new_review) # refresh loads scalar attributes, not necessarily relationships
    # If Review schema has `user: UserSchema`, you might need to query it with options(joinedload(models.Review.user))
    # or manually assign: new_review.user = current_user (if the relationship is set up for this)
    return new_review


@router.get("/places/{place_id}/reviews", response_model=List[schemas.review.Review])
def read_reviews_for_place(
    place_id: int,
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100), # Example: default 20, min 1, max 100
    db: Session = Depends(get_db)
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Place with id {place_id} not found")

    reviews = crud.review.get_reviews_by_place(db, place_id=place_id, skip=skip, limit=limit)
    return reviews

@router.get("/reviews/{review_id}", response_model=schemas.review.Review)
def read_single_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    db_review = crud.review.get_review(db, review_id=review_id)
    if db_review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return db_review


@router.put("/reviews/{review_id}", response_model=schemas.review.Review)
def update_own_review(
    review_id: int,
    review_in: schemas.review.ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    # crud.review.update_review will check for ownership and return "NotAuthorized" or the updated object
    updated_review_result = crud.review.update_review(
        db=db, review_id=review_id, review_update=review_in, user_id=current_user.id
    )

    if updated_review_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if updated_review_result == "NotAuthorized":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this review")

    return updated_review_result


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    # crud.review.delete_review will check for ownership
    deleted_review_result = crud.review.delete_review(db=db, review_id=review_id, user_id=current_user.id)

    if deleted_review_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if deleted_review_result == "NotAuthorized":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this review")

    # No content to return for 204
    return

# Optional: Get reviews by a specific user (e.g., for a user's profile page)
@router.get("/users/{user_id}/reviews", response_model=List[schemas.review.Review])
def read_reviews_by_user(
    user_id: int,
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
    # Add auth if this should be protected or only for admin/self
    # current_user: models.user.User = Depends(get_current_active_user)
):
    # Check if user exists
    db_user = crud.user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")

    reviews = crud.review.get_reviews_by_user(db, user_id=user_id, skip=skip, limit=limit)
    return reviews
