from fastapi import APIRouter, Depends, HTTPException, status, Query # Removed HTTPException
from sqlalchemy.orm import Session
from typing import List, Any, Optional

from app import schemas
from app.db.database import get_db
from app.core.security import get_current_active_user, require_role # Added require_role
from app.schemas.user import UserRole # Added UserRole
from app.models.user import User as UserModel
from app.services.place_service import PlaceService # Import PlaceService

router = APIRouter()

# Dependency to get PlaceService instance
def get_place_service(db: Session = Depends(get_db)) -> PlaceService:
    return PlaceService(db)


@router.post("/", response_model=schemas.Place, status_code=status.HTTP_201_CREATED)
def create_place(
    *,
    place_service: PlaceService = Depends(get_place_service),
    place_in: schemas.PlaceCreate,
    current_user: UserModel = Depends(require_role([UserRole.ADMIN, UserRole.EDITOR]))
) -> Any:
    """
    Create new place. Requires ADMIN or EDITOR role.
    """
    place = place_service.create_new_place(place_in=place_in)
    return place


@router.get("/", response_model=List[schemas.Place])
def read_places(
    place_service: PlaceService = Depends(get_place_service),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(
        None, description="Filter places by category (case-insensitive partial match)"
    ),
    min_rating: Optional[float] = Query(
        None, ge=0.0, le=5.0, description="Filter places by minimum average rating"
    ),
) -> Any:
    """
    Retrieve places with optional filtering by category and minimum rating.
    Publicly accessible.
    """
    places = place_service.get_all_places(
        skip=skip, limit=limit, category=category, min_rating=min_rating
    )
    return places


@router.get("/{place_id}", response_model=schemas.Place)
def read_place_by_id(
    place_id: int,
    place_service: PlaceService = Depends(get_place_service),
) -> Any:
    """
    Get a specific place by id. Publicly accessible.
    """
    place = place_service.get_place_by_id(place_id=place_id)
    # Service method raises HTTPException 404 if not found
    return place


@router.put("/{place_id}", response_model=schemas.Place)
def update_place(
    *,
    place_id: int,
    place_in: schemas.PlaceUpdate,
    place_service: PlaceService = Depends(get_place_service),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN, UserRole.EDITOR]))
) -> Any:
    """
    Update a place. Requires ADMIN or EDITOR role.
    """
    # Additional ownership check could be added here or in the service if needed,
    # e.g., if editors can only edit places they created.
    # For now, ADMIN and EDITOR can edit any place.
    place = place_service.update_existing_place(place_id=place_id, place_in=place_in)
    # Service method raises HTTPException 404 if not found
    return place


@router.delete("/{place_id}", response_model=schemas.Place)
def delete_place(
    *,
    place_id: int,
    place_service: PlaceService = Depends(get_place_service),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN])) # Only ADMIN can delete
) -> Any:
    """
    Delete a place. Requires ADMIN role.
    """
    deleted_place = place_service.delete_existing_place(place_id=place_id)
    # Service method raises HTTPException 404 if not found
    return deleted_place
