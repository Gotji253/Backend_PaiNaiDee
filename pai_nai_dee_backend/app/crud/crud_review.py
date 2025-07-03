from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models # Adjusted import
from ..schemas import review as review_schema # Adjusted import and aliased

def get_review(db: Session, review_id: int) -> Optional[models.review.Review]:
    return db.query(models.review.Review).filter(models.review.Review.id == review_id).first()

def get_reviews_by_place(
    db: Session, place_id: int, skip: int = 0, limit: int = 100
) -> List[models.review.Review]:
    return (
        db.query(models.review.Review)
        .filter(models.review.Review.place_id == place_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_reviews_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.review.Review]:
    return (
        db.query(models.review.Review)
        .filter(models.review.Review.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_review(
    db: Session, review: review_schema.ReviewCreate, user_id: int
) -> models.review.Review:
    db_review = models.review.Review(
        **review.model_dump(),  # place_id is in review.model_dump()
        user_id=user_id
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def update_review(
    db: Session, review_id: int, review_update: review_schema.ReviewUpdate, user_id: int
) -> Optional[models.review.Review]:
    db_review = db.query(models.review.Review).filter(models.review.Review.id == review_id).first()

    if not db_review:
        return None

    # Check for ownership
    if db_review.user_id != user_id:
        # Or raise an exception (e.g., HTTPException(status.HTTP_403_FORBIDDEN, detail="Not authorized"))
        # For CRUD layer, returning None is often preferred, router handles HTTP exception.
        return "NotAuthorized" # Special string to indicate authorization failure

    update_data = review_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_review, field, value)

    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

def delete_review(db: Session, review_id: int, user_id: int) -> Optional[models.review.Review | str]:
    db_review = db.query(models.review.Review).filter(models.review.Review.id == review_id).first()

    if not db_review:
        return None # Not found

    # Check for ownership or superuser (example if you add superuser logic here)
    # if db_review.user_id != user_id and not current_user.is_superuser:
    if db_review.user_id != user_id:
        return "NotAuthorized" # Special string for authorization failure

    db.delete(db_review)
    db.commit()
    return db_review # Return the deleted object (now detached from session)
