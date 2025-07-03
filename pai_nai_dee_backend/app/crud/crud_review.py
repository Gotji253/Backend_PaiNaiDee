from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate

# from app.crud.crud_place import place as crud_place # For updating place average rating


class CRUDReview:
    def get_review(self, db: Session, review_id: int) -> Optional[Review]:
        return db.query(Review).filter(Review.id == review_id).first()

    def get_reviews_by_place(
        self, db: Session, place_id: int, skip: int = 0, limit: int = 20
    ) -> List[Review]:
        return (
            db.query(Review)
            .filter(Review.place_id == place_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_reviews_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[Review]:
        return (
            db.query(Review)
            .filter(Review.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_review(
        self, db: Session, *, review_in: ReviewCreate, user_id: int
    ) -> Review:
        db_review = Review(
            rating=review_in.rating,
            comment=review_in.comment,
            place_id=review_in.place_id,
            user_id=user_id,  # Set by the system from authenticated user
        )
        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        # After creating a review, you might want to update the place's average rating.
        # This could be done here, or via a database trigger, or a background task/event.
        # For now, let's assume a service layer or a subsequent call handles this.
        # Example: crud_place.update_place_average_rating(db, place_id=db_review.place_id)

        return db_review

    def update_review(
        self, db: Session, *, db_review: Review, review_in: ReviewUpdate
    ) -> Review:
        update_data = review_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_review, field, value)

        db.add(db_review)
        db.commit()
        db.refresh(db_review)

        # Similar to create, updating a review might require recalculating the place's average rating.
        # Example: crud_place.update_place_average_rating(db, place_id=db_review.place_id)

        return db_review

    def delete_review(self, db: Session, review_id: int) -> Optional[Review]:
        review = db.query(Review).get(review_id)
        if review:
            # place_id = review.place_id # Store before deleting for rating update
            db.delete(review)
            db.commit()
            # After deleting a review, update the place's average rating.
            # Example: crud_place.update_place_average_rating(db, place_id=place_id)
        return review


review = CRUDReview()
