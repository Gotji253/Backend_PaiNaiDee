from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud # Adjusted import
from .. import models # Adjusted import
from .. import schemas # Adjusted import
from ..database import get_db # Adjusted import
from ..auth.dependencies import get_current_active_user # For protected routes

router = APIRouter()

@router.post(
    "/{place_id}",
    response_model=schemas.favorite.FavoriteResponse, # Custom response
    status_code=status.HTTP_200_OK # Or 201 if creating a new favorite link
)
def add_place_to_favorites(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Check if already favorited before adding to avoid issues, though SQLAlchemy handles set semantics
    is_already_favorited = crud.favorite.is_place_favorited_by_user(db, user_id=current_user.id, place_id=place_id)

    if is_already_favorited:
        return schemas.favorite.FavoriteResponse(
            message="Place is already in favorites.",
            user_id=current_user.id,
            place_id=place_id,
            is_favorited=True
        )

    user_with_favs = crud.favorite.add_favorite(db=db, user_id=current_user.id, place_id=place_id)
    if not user_with_favs: # Should not happen if user and place checks are done
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not add favorite")

    return schemas.favorite.FavoriteResponse(
        message="Place added to favorites successfully.",
        user_id=current_user.id,
        place_id=place_id,
        is_favorited=True
    )

@router.delete(
    "/{place_id}",
    response_model=schemas.favorite.FavoriteResponse
)
def remove_place_from_favorites(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    is_favorited = crud.favorite.is_place_favorited_by_user(db, user_id=current_user.id, place_id=place_id)
    if not is_favorited:
         return schemas.favorite.FavoriteResponse(
            message="Place is not in favorites.",
            user_id=current_user.id,
            place_id=place_id,
            is_favorited=False
        )

    user_after_removal = crud.favorite.remove_favorite(db=db, user_id=current_user.id, place_id=place_id)
    if not user_after_removal: # Should generally not happen if place was confirmed favorited
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not remove favorite")

    return schemas.favorite.FavoriteResponse(
        message="Place removed from favorites successfully.",
        user_id=current_user.id,
        place_id=place_id,
        is_favorited=False
    )

@router.get(
    "/users/me/favorites",
    response_model=List[schemas.place.Place] # Returns a list of Place objects
)
def get_my_favorite_places(
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    favorite_places = crud.favorite.get_user_favorite_places(db, user_id=current_user.id)
    if favorite_places is None: # Should not happen for an authenticated user
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found, unable to retrieve favorites.")
    return favorite_places

# Optional: Check if a specific place is favorited by the current user
@router.get("/{place_id}/is-favorited", response_model=bool)
def check_if_place_is_favorited(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user)
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    return crud.favorite.is_place_favorited_by_user(db, user_id=current_user.id, place_id=place_id)
