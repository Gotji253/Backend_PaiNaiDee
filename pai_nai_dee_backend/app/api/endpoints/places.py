from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app import schemas # Updated import
from app import crud # Updated import
from app.db.database import get_db
from app.core.security import get_current_active_user # For protected routes
from app.models.user import User as UserModel # For current user type hint

router = APIRouter()

@router.post("/", response_model=schemas.Place, status_code=status.HTTP_201_CREATED)
def create_place(
    *,
    db: Session = Depends(get_db),
    place_in: schemas.PlaceCreate,
    current_user: UserModel = Depends(get_current_active_user) # Place creation needs auth
) -> Any:
    """
    Create new place. Requires authentication.
    """
    place = crud.crud_place.create_place(db=db, place_in=place_in)
    return place

@router.get("/", response_model=List[schemas.Place])
def read_places(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter places by category (case-insensitive partial match)"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Filter places by minimum average rating")
) -> Any:
    """
    Retrieve places with optional filtering by category and minimum rating.
    """
    places = crud.crud_place.get_places(db, skip=skip, limit=limit, category=category, min_rating=min_rating)
    return places

@router.get("/{place_id}", response_model=schemas.Place)
def read_place_by_id(
    place_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific place by id.
    """
    place = crud.crud_place.get_place(db, place_id=place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found",
        )
    return place

@router.put("/{place_id}", response_model=schemas.Place)
def update_place(
    *,
    db: Session = Depends(get_db),
    place_id: int,
    place_in: schemas.PlaceUpdate,
    current_user: UserModel = Depends(get_current_active_user) # Place update needs auth
) -> Any:
    """
    Update a place. Requires authentication.
    TODO: Add ownership or admin role check.
    """
    db_place = crud.crud_place.get_place(db, place_id=place_id)
    if not db_place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Place not found",
        )
    place = crud.crud_place.update_place(db=db, db_place=db_place, place_in=place_in)
    return place

@router.delete("/{place_id}", response_model=schemas.Place)
def delete_place(
    *,
    db: Session = Depends(get_db),
    place_id: int,
    current_user: UserModel = Depends(get_current_active_user) # Place deletion needs auth
) -> Any:
    """
    Delete a place. Requires authentication.
    TODO: Add ownership or admin role check.
    """
    place_to_delete = crud.crud_place.get_place(db, place_id=place_id)
    if not place_to_delete:
        raise HTTPException(status_code=404, detail="Place not found")

    deleted_place = crud.crud_place.delete_place(db=db, place_id=place_id)
    if not deleted_place: # Should not happen if previous check passed
        raise HTTPException(status_code=404, detail="Place not found during delete operation")
    return deleted_place
