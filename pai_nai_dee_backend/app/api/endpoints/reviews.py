from fastapi import APIRouter, Depends, HTTPException, status # Query removed, HTTPException might be used for auth here
from sqlalchemy.orm import Session
from typing import List, Any

from app import schemas
from app.db.database import get_db
from app.models.user import User as UserModel
from app.core.security import get_current_active_user, require_role # Added require_role
from app.schemas.user import UserRole # Added UserRole
from app.services.review_service import ReviewService # Import ReviewService

router = APIRouter()

# Dependency to get ReviewService instance
def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    return ReviewService(db)


@router.post("/", response_model=schemas.Review, status_code=status.HTTP_201_CREATED)
def create_review(
    *,
    review_service: ReviewService = Depends(get_review_service),
    review_in: schemas.ReviewCreate,
    current_user: UserModel = Depends(get_current_active_user), # Any authenticated user can create
) -> Any:
    """
    Create new review for a place. User must be authenticated.
    Service handles checking place existence and updating place average rating.
    """
    review = review_service.create_new_review(review_in=review_in, current_user=current_user)
    return review


@router.get("/place/{place_id}", response_model=List[schemas.Review])
def read_reviews_for_place(
    place_id: int,
    review_service: ReviewService = Depends(get_review_service),
    skip: int = 0,
    limit: int = 20
) -> Any:
    """
    Get all reviews for a specific place. Publicly accessible.
    """
    # Service can optionally check if place_id is valid if desired, or just return empty list.
    # For now, ReviewService.get_reviews_for_place does not check place existence.
    reviews = review_service.get_reviews_for_place(
        place_id=place_id, skip=skip, limit=limit
    )
    return reviews


@router.get("/user/{user_id}", response_model=List[schemas.Review])
def read_reviews_by_user(
    user_id: int,
    review_service: ReviewService = Depends(get_review_service),
    skip: int = 0,
    limit: int = 20,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get all reviews written by a specific user.
    A user can see their own reviews. An admin can see any user's reviews.
    """
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view these reviews.",
        )
    # Service can optionally check if user_id is valid.
    reviews = review_service.get_reviews_by_user_id(
        user_id=user_id, skip=skip, limit=limit
    )
    return reviews


@router.get("/{review_id}", response_model=schemas.Review)
def read_review_by_id(
    review_id: int,
    review_service: ReviewService = Depends(get_review_service)
) -> Any:
    """
    Get a specific review by its ID. Publicly accessible.
    """
    review = review_service.get_review_by_id(review_id=review_id)
    # Service method raises HTTPException 404 if not found
    return review


@router.put("/{review_id}", response_model=schemas.Review)
def update_review(
    *,
    review_id: int,
    review_in: schemas.ReviewUpdate,
    review_service: ReviewService = Depends(get_review_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Update a review. User must be the author of the review.
    Service handles checking review existence, ownership, and updating place average rating.
    """
    # The service method `update_existing_review` will handle the ownership check.
    review = review_service.update_existing_review(
        review_id=review_id, review_in=review_in, current_user=current_user
    )
    return review


@router.delete("/{review_id}", response_model=schemas.Review)
def delete_review(
    *,
    review_id: int,
    review_service: ReviewService = Depends(get_review_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Delete a review. User must be the author or an admin.
    Service handles checking review existence, ownership/admin rights, and updating place average rating.
    """
    # The service method `delete_existing_review` will handle the ownership/admin check.
    deleted_review = review_service.delete_existing_review(
        review_id=review_id, current_user=current_user
    )
    return deleted_review
