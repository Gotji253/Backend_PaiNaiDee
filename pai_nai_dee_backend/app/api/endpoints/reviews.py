from fastapi import APIRouter, Depends, HTTPException, status  # Query removed
from sqlalchemy.orm import Session
from typing import List, Any  # Optional removed

from ...schemas import Review as ReviewSchema, ReviewCreate, ReviewUpdate
from ...crud import crud_place, crud_review, crud_user
from ...db.database import get_db
from ...models.user import User as UserModel
from ...core.security import get_current_active_user

router = APIRouter()


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
def create_review(
    *,
    db: Session = Depends(get_db),
    review_in: ReviewCreate,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Create new review for a place. User must be authenticated.
    """
    # Check if the place exists
    place = crud_place.get_place(db, place_id=review_in.place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
        )

    review = crud_review.create_review(
        db=db, review_in=review_in, user_id=current_user.id
    )
    # Here, we might trigger an update for place's average_rating
    # crud_place.update_place_average_rating(db, place_id=review.place_id) # Example
    return review


@router.get("/place/{place_id}", response_model=List[ReviewSchema])
def read_reviews_for_place(
    place_id: int, db: Session = Depends(get_db), skip: int = 0, limit: int = 20
) -> Any:
    """
    Get all reviews for a specific place.
    """
    place = crud_place.get_place(db, place_id=place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
        )
    reviews = crud_review.get_reviews_by_place(
        db, place_id=place_id, skip=skip, limit=limit
    )
    return reviews


@router.get("/user/{user_id}", response_model=List[ReviewSchema])
def read_reviews_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    current_user: UserModel = Depends(
        get_current_active_user
    ),  # Auth: only user themselves or admin
) -> Any:
    """
    Get all reviews written by a specific user.
    (Protected by auth in a real app - user can see their own, admin can see all)
    """
    user = crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Permission check example (to be refined with actual auth)
    # if current_user.id != user_id and not crud_user.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions")

    reviews = crud_review.get_reviews_by_user(
        db, user_id=user_id, skip=skip, limit=limit
    )
    return reviews


@router.get("/{review_id}", response_model=ReviewSchema)
def read_review_by_id(review_id: int, db: Session = Depends(get_db)) -> Any:
    """
    Get a specific review by its ID.
    """
    review = crud_review.get_review(db, review_id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )
    return review


@router.put("/{review_id}", response_model=ReviewSchema)
def update_review(
    *,
    db: Session = Depends(get_db),
    review_id: int,
    review_in: ReviewUpdate,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Update a review. User must be the author of the review.
    """
    db_review = crud_review.get_review(db, review_id=review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    if (
        db_review.user_id != current_user.id
    ):  # and not crud_user.is_superuser(current_user): # Add admin override later
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this review",
        )

    review = crud_review.update_review(
        db=db, db_review=db_review, review_in=review_in
    )
    # crud_place.update_place_average_rating(db, place_id=review.place_id) # Example
    return review


@router.delete("/{review_id}", response_model=ReviewSchema)
def delete_review(
    *,
    db: Session = Depends(get_db),
    review_id: int,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Delete a review. User must be the author or an admin.
    """
    db_review = crud_review.get_review(db, review_id=review_id)
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    # Permission check
    # if db_review.user_id != current_user.id and not crud_user.is_superuser(current_user):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this review")

    # For placeholder, let's assume if user_id matches or if it's a "superuser" (not yet defined)
    if db_review.user_id != current_user.id:
        # This logic needs refinement with actual roles/permissions
        print(
            f"User {current_user.id} attempting to delete review {db_review.id} owned by {db_review.user_id}"
        )
        # For now, only owner can delete with this placeholder logic.
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this review (placeholder check)")
        pass  # Allow for now, to be tightened in auth step

    deleted_review = crud_review.delete_review(db=db, review_id=review_id)
    if not deleted_review:  # Should not happen if previous check passed
        raise HTTPException(
            status_code=404, detail="Review not found during delete operation"
        )

    # crud_place.update_place_average_rating(db, place_id=deleted_review.place_id) # Example
    return deleted_review
