import logging # Added logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app import crud, schemas
from app.models.review import Review as ReviewModel
from app.models.user import User as UserModel
from app.services.place_service import PlaceService # To update place ratings

logger = logging.getLogger(__name__) # Added logger instance

class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        # Instantiate other services if needed directly, or set up a more complex DI system later
        self.place_service = PlaceService(db)

    def create_new_review(self, review_in: schemas.ReviewCreate, current_user: UserModel) -> ReviewModel:
        """
        Creates a new review for a place.
        Ensures the place exists and updates the place's average rating.
        """
        # Ensure place exists (PlaceService.get_place_by_id raises 404 if not found)
        self.place_service.get_place_by_id(review_in.place_id)

        review = crud.review.create_review(db=self.db, review_in=review_in, user_id=current_user.id)

        # Update average rating for the place
        try:
            self.place_service.update_place_average_rating(place_id=review.place_id)
        except HTTPException as e:
            # Log this error, as review creation succeeded but rating update failed.
            # Depending on policy, this might or might not be a critical failure.
            # For now, we'll let the review creation succeed and log the rating update issue.
            logger.error(f"Error updating place average rating for place {review.place_id} after review creation: {e.detail}", exc_info=True)
            # Consider if you need to reraise or handle differently.

        return review

    def get_review_by_id(self, review_id: int) -> Optional[ReviewModel]:
        """
        Retrieves a review by its ID.
        """
        review = crud.review.get_review(self.db, review_id=review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )
        return review

    def get_reviews_for_place(self, place_id: int, skip: int = 0, limit: int = 20) -> List[ReviewModel]:
        """
        Retrieves reviews for a specific place.
        """
        # Ensure place exists (optional, depends if you want to 404 on non-existent place for reviews list)
        # self.place_service.get_place_by_id(place_id)
        return crud.review.get_reviews_by_place(self.db, place_id=place_id, skip=skip, limit=limit)

    def get_reviews_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ReviewModel]:
        """
        Retrieves reviews written by a specific user.
        """
        # Ensure user exists (optional, could be done in router or here)
        # user = crud.user.get_user(self.db, user_id=user_id)
        # if not user:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found when fetching reviews")
        return crud.review.get_reviews_by_user(self.db, user_id=user_id, skip=skip, limit=limit)

    def update_existing_review(
        self, review_id: int, review_in: schemas.ReviewUpdate, current_user: UserModel
    ) -> Optional[ReviewModel]:
        """
        Updates an existing review. User must be the author.
        Updates the place's average rating.
        """
        db_review = self.get_review_by_id(review_id) # Raises 404 if not found
        if not db_review: # Should be caught by get_review_by_id
            return None

        if db_review.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this review.",
            )

        updated_review = crud.review.update_review(db=self.db, db_review=db_review, review_in=review_in)

        # Update average rating for the place
        try:
            self.place_service.update_place_average_rating(place_id=updated_review.place_id)
        except HTTPException as e:
            logger.error(f"Error updating place average rating for place {updated_review.place_id} after review update: {e.detail}", exc_info=True)

        return updated_review

    def delete_existing_review(self, review_id: int, current_user: UserModel) -> Optional[ReviewModel]:
        """
        Deletes a review. User must be the author or an admin.
        Updates the place's average rating.
        """
        db_review = self.get_review_by_id(review_id) # Raises 404 if not found
        if not db_review: # Should be caught by get_review_by_id
            return None

        # Authorization: User is author OR current_user is ADMIN
        # (Assuming UserRole is available on current_user model, which it is from previous steps)
        if db_review.user_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this review.",
            )

        place_id_of_deleted_review = db_review.place_id
        deleted_review_obj = crud.review.delete_review(db=self.db, review_id=review_id)

        if deleted_review_obj:
            # Update average rating for the place
            try:
                self.place_service.update_place_average_rating(place_id=place_id_of_deleted_review)
            except HTTPException as e:
                 logger.error(f"Error updating place average rating for place {place_id_of_deleted_review} after review deletion: {e.detail}", exc_info=True)

        return deleted_review_obj
