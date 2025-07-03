from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models
from .. import schemas
from fastapi import HTTPException, status
from sqlalchemy import func

def create_review(db: Session, review: schemas.ReviewCreate, user_id: int) -> models.Review:
    """
    Create a new review for a place.
    """
    # Check if the place exists
    db_place = db.query(models.Place).filter(models.Place.id == review.place_id).first()
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Optional: Check if user has already reviewed this place (if one review per user per place)
    # existing_review = db.query(models.Review).filter(models.Review.place_id == review.place_id, models.Review.user_id == user_id).first()
    # if existing_review:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has already reviewed this place")

    db_review = models.Review(
        **review.model_dump(),  # Pydantic V2
        user_id=user_id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    update_place_average_rating(db, review.place_id)

    # Log activity
    activity_log_entry = models.UserActivityLog(
        user_id=user_id,
        activity_type="create_review",
        place_id=review.place_id,
        details=f"Review ID: {db_review.id}"
    )
    db.add(activity_log_entry)
    db.commit()

    return db_review

def get_reviews_for_place(db: Session, place_id: int, skip: int = 0, limit: int = 20) -> List[models.Review]:
    """
    Get all reviews for a specific place.
    """
    return db.query(models.Review).filter(models.Review.place_id == place_id).offset(skip).limit(limit).all()

def get_review_by_id(db: Session, review_id: int) -> Optional[models.Review]:
    """
    Get a single review by its ID.
    """
    return db.query(models.Review).filter(models.Review.id == review_id).first()

def delete_review(db: Session, review_id: int, user_id: int) -> Optional[models.Review]:
    """
    Delete a review. Only the owner or an admin (not implemented yet) can delete.
    """
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    # TODO: Implement admin check in future. For now, only owner.
    if db_review.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this review")

    place_id_of_deleted_review = db_review.place_id
    db.delete(db_review)
    db.commit()

    update_place_average_rating(db, place_id_of_deleted_review)

    # Log activity (optional for delete, but can be useful)
    activity_log_entry = models.UserActivityLog(
        user_id=user_id,
        activity_type="delete_review",
        place_id=place_id_of_deleted_review, # Log which place it was for
        details=f"Deleted Review ID: {review_id}"
    )
    db.add(activity_log_entry)
    db.commit()

    return db_review # Return the deleted review data (or just a confirmation)

# Function to update average rating for a place
def update_place_average_rating(db: Session, place_id: int):
    """
    Calculates and updates the average rating and review count for a place.
    """
    db_place = db.query(models.Place).filter(models.Place.id == place_id).first()
    if not db_place:
        # This should ideally not happen if called from create/delete review
        # as place existence is checked there or review wouldn't exist.
        print(f"Warning: Place with ID {place_id} not found during average rating update.")
        return

    # Calculate average rating and count
    result = db.query(
        func.avg(models.Review.rating).label("average_rating"),
        func.count(models.Review.id).label("review_count")
    ).filter(models.Review.place_id == place_id).one()

    db_place.average_rating = result.average_rating if result.average_rating is not None else 0.0
    db_place.review_count = result.review_count if result.review_count is not None else 0

    db.add(db_place)
    db.commit()
    db.refresh(db_place)
