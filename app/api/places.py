from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps # For authentication dependencies
from app.db.session import get_db # For database session

router = APIRouter()

@router.post("/", response_model=schemas.Place, status_code=status.HTTP_201_CREATED)
def create_place(
    *,
    db: Session = Depends(get_db),
    place_in: schemas.PlaceCreate,
    current_user: models.User = Depends(deps.get_current_active_user) # Requires auth
) -> Any:
    """
    Create a new place. Requires authentication.
    (Note: Currently, any authenticated user can create a place.
    You might want to restrict this to superusers or specific roles later.)
    """
    # Optionally, check if a place with the same name already exists
    # existing_place = crud.place.get_by_name(db, name=place_in.name)
    # if existing_place:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="A place with this name already exists.",
    #     )
    place = crud.place.create(db=db, obj_in=place_in)
    return place

@router.get("/", response_model=List[schemas.Place])
def read_places(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    category: str = Query(None, description="Filter places by category")
) -> Any:
    """
    Retrieve all places with optional pagination and category filter.
    This endpoint is public.
    """
    if category:
        places = crud.place.get_multi_by_category(db, category=category, skip=skip, limit=limit)
    else:
        places = crud.place.get_multi(db, skip=skip, limit=limit)
    return places

@router.get("/{place_id}", response_model=schemas.Place)
def read_place(
    *,
    db: Session = Depends(get_db),
    place_id: int,
) -> Any:
    """
    Get a specific place by ID. Public.
    """
    place = crud.place.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return place

@router.put("/{place_id}", response_model=schemas.Place)
def update_place(
    *,
    db: Session = Depends(get_db),
    place_id: int,
    place_in: schemas.PlaceUpdate,
    current_user: models.User = Depends(deps.get_current_active_user) # Requires auth
) -> Any:
    """
    Update a place. Requires authentication.
    (Note: Currently, any authenticated user can update any place.
    You might want to restrict this to the creator or superusers later.)
    """
    place = crud.place.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Add authorization logic here if needed, e.g.,
    # if place.owner_id != current_user.id and not current_user.is_superuser:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    place = crud.place.update(db=db, db_obj=place, obj_in=place_in)
    return place

@router.delete("/{place_id}", response_model=schemas.Place) # Or just status_code=204 NO CONTENT
def delete_place(
    *,
    db: Session = Depends(get_db),
    place_id: int,
    current_user: models.User = Depends(deps.get_current_active_user) # Requires auth
) -> Any:
    """
    Delete a place. Requires authentication.
    (Note: Similar to update, consider authorization rules.)
    """
    place = crud.place.get(db=db, id=place_id)
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")

    # Add authorization logic here if needed

    deleted_place = crud.place.remove(db=db, id=place_id)
    return deleted_place # Returns the deleted object, or you can return a message/status code.
