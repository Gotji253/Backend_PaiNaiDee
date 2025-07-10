from sqlalchemy.orm import Session
from typing import List, Optional

from app.crud.base import CRUDBase
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewUpdate

class CRUDReview(CRUDBase[Review, ReviewCreate, ReviewUpdate]):
    def create_with_owner_and_place(
        self, db: Session, *, obj_in: ReviewCreate, owner_id: int, place_id: int
    ) -> Review:
        # Ensure the place_id from obj_in matches the place_id parameter,
        # or decide which one takes precedence. Here, using the one from obj_in.
        db_obj = Review(
            rating=obj_in.rating,
            comment=obj_in.comment,
            owner_id=owner_id,
            place_id=obj_in.place_id # or use place_id parameter directly
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        return (
            db.query(self.model)
            .filter(Review.owner_id == owner_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_place(
        self, db: Session, *, place_id: int, skip: int = 0, limit: int = 100
    ) -> List[Review]:
        return (
            db.query(self.model)
            .filter(Review.place_id == place_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # Update method is inherited from CRUDBase.
    # If specific logic for review update is needed (e.g., disallowing place_id/owner_id change),
    # it can be overridden here. For now, CRUDBase.update will handle it.
    # Note: The ReviewUpdate schema already makes place_id and owner_id non-updatable
    # by not including them.

review = CRUDReview(Review)
