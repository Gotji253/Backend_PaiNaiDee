from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud # Adjusted import
from .. import models # Adjusted import
from .. import schemas # Adjusted import
from ..database import get_db # Adjusted import
from ..auth.dependencies import get_current_active_user # For protected routes

router = APIRouter()

@router.post("/", response_model=schemas.place.Place, status_code=status.HTTP_201_CREATED)
def create_new_place(
    place_in: schemas.place.PlaceCreate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user) # Require authentication
):
    # Here you could add logic to associate the place with the current_user if your model supports it
    # e.g., by passing current_user.id to crud.place.create_place
    # For now, crud.place.create_place does not expect a user_id.
    new_place = crud.place.create_place(db=db, place=place_in)
    return new_place

@router.get("/", response_model=List[schemas.place.Place])
def read_places(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    places = crud.place.get_places(db, skip=skip, limit=limit, category=category)
    return places

@router.get("/{place_id}", response_model=schemas.place.Place)
def read_place(
    place_id: int,
    db: Session = Depends(get_db)
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if db_place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return db_place

@router.put("/{place_id}", response_model=schemas.place.Place)
def update_existing_place(
    place_id: int,
    place_in: schemas.place.PlaceUpdate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user) # Require authentication
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Add authorization logic here if needed:
    # e.g., if user can only update places they created.
    # if db_place.submitter_id != current_user.id:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this place")

    updated_place = crud.place.update_place(db=db, place_id=place_id, place_update=place_in)
    return updated_place

@router.delete("/{place_id}", response_model=schemas.place.Place) # Or return a 204 No Content
def delete_existing_place(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_active_user) # Require authentication
):
    db_place = crud.place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Add authorization logic here:
    # e.g., if user can only delete places they created or if they are a superuser.
    # if db_place.submitter_id != current_user.id and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this place")

    deleted_place = crud.place.delete_place(db=db, place_id=place_id)
    if deleted_place is None: # Should not happen if previous check passed, but good practice
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found for deletion")
    return deleted_place # FastAPI will return 200 OK by default. Consider 204 if no body.

# If returning 204 No Content for DELETE:
# from fastapi import Response
# @router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_existing_place(
#     place_id: int,
#     db: Session = Depends(get_db),
#     current_user: models.user.User = Depends(get_current_active_user)
# ):
#     # ... (checks as above)
#     crud.place.delete_place(db=db, place_id=place_id)
#     return Response(status_code=status.HTTP_204_NO_CONTENT)
