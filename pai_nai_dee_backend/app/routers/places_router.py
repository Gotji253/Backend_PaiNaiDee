from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..services import places_service # Will be aliased as places in __init__.py
from .. import schemas # Access as schemas.Place, schemas.PlaceCreate etc.
from ..models.users import User as UserModel # For auth dependency
from ..auth import get_current_active_user # Import the real dependency

router = APIRouter(
    prefix="/api/places",
    tags=["places"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Place, status_code=status.HTTP_201_CREATED)
def create_place_endpoint(
    place: schemas.PlaceCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect place creation
):
    # Assuming only authenticated (e.g. admin/privileged) users can create places for now
    if not current_user.is_superuser: # Example protection
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to create a place.")
    return places_service.create_place(db=db, place=place)

@router.get("/", response_model=List[schemas.Place])
def read_places_endpoint(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search query in name and description"),
    db: Session = Depends(get_db)
):
    # Listing places is public
    places = places_service.get_places(db, skip=skip, limit=limit, category=category, search_query=search)
    return places

@router.get("/{place_id}", response_model=schemas.Place)
def read_place_endpoint(
    place_id: int,
    db: Session = Depends(get_db)
):
    # Viewing a specific place is public
    db_place = places_service.get_place(db, place_id=place_id)
    if db_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return db_place

@router.put("/{place_id}", response_model=schemas.Place)
def update_place_endpoint(
    place_id: int,
    place: schemas.PlaceUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect update
):
    if not current_user.is_superuser: # Example protection
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to update this place.")

    updated_place = places_service.update_place(db, place_id=place_id, place_update=place)
    if updated_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return updated_place

@router.delete("/{place_id}", response_model=schemas.Place)
def delete_place_endpoint(
    place_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect deletion
):
    if not current_user.is_superuser: # Example protection
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete this place.")

    deleted_place = places_service.delete_place(db, place_id=place_id)
    if deleted_place is None:
        raise HTTPException(status_code=404, detail="Place not found")
    return deleted_place
