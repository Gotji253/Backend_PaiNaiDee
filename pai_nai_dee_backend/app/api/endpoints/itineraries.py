from fastapi import APIRouter, Depends, HTTPException, status # HTTPException might be used for auth
from sqlalchemy.orm import Session
from typing import List, Any

from app import schemas
from app.db.database import get_db
from app.models.user import User as UserModel
from app.core.security import get_current_active_user, require_role # Added require_role
from app.schemas.user import UserRole # Added UserRole for potential admin access
from app.services.itinerary_service import ItineraryService # Import ItineraryService

router = APIRouter()

# Dependency to get ItineraryService instance
def get_itinerary_service(db: Session = Depends(get_db)) -> ItineraryService:
    return ItineraryService(db)


@router.post("/", response_model=schemas.Itinerary, status_code=status.HTTP_201_CREATED)
def create_itinerary(
    *,
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    itinerary_in: schemas.ItineraryCreate,
    current_user: UserModel = Depends(get_current_active_user), # Any authenticated user
) -> Any:
    """
    Create new itinerary for the current authenticated user.
    Service handles validation of place_ids.
    """
    itinerary = itinerary_service.create_new_itinerary(itinerary_in=itinerary_in, current_user=current_user)
    # Service method raises HTTPException if places not found
    return itinerary


@router.get("/my-itineraries", response_model=List[schemas.Itinerary])
def read_my_itineraries(
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    skip: int = 0,
    limit: int = 20,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get all itineraries for the current authenticated user.
    """
    itineraries = itinerary_service.get_all_itineraries_for_user(
        current_user=current_user, skip=skip, limit=limit
    )
    return itineraries


@router.get("/{itinerary_id}", response_model=schemas.Itinerary)
def read_itinerary_by_id(
    itinerary_id: int,
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific itinerary by id.
    User must be the owner or an admin.
    """
    itinerary = itinerary_service.get_itinerary_by_id_for_user(
        itinerary_id=itinerary_id, current_user=current_user
    )
    # Service method handles 404 and ownership/admin check
    return itinerary


@router.put("/{itinerary_id}", response_model=schemas.Itinerary)
def update_itinerary(
    *,
    itinerary_id: int,
    itinerary_in: schemas.ItineraryUpdate,
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Update an itinerary. User must be the owner.
    Service handles ownership check and validation of place_ids.
    """
    itinerary = itinerary_service.update_existing_itinerary(
        itinerary_id=itinerary_id, itinerary_in=itinerary_in, current_user=current_user
    )
    # Service method handles 404, ownership, and place validation issues
    return itinerary


@router.delete("/{itinerary_id}", response_model=schemas.Itinerary)
def delete_itinerary(
    *,
    itinerary_id: int,
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Delete an itinerary. User must be the owner or an admin.
    Service handles ownership/admin check.
    """
    deleted_itinerary = itinerary_service.delete_existing_itinerary(
        itinerary_id=itinerary_id, current_user=current_user
    )
    # Service method handles 404 and ownership/admin check
    return deleted_itinerary


# Optional: Endpoints to manage places within an itinerary
@router.post("/{itinerary_id}/places/{place_id}", response_model=schemas.Itinerary)
def add_place_to_itinerary_endpoint(
    itinerary_id: int,
    place_id: int,
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Adds a place to an itinerary. User must be the owner of the itinerary.
    Service handles ownership and existence checks for itinerary and place.
    """
    updated_itinerary = itinerary_service.add_place_to_existing_itinerary(
        itinerary_id=itinerary_id, place_id=place_id, current_user=current_user
    )
    return updated_itinerary


@router.delete("/{itinerary_id}/places/{place_id}", response_model=schemas.Itinerary)
def remove_place_from_itinerary_endpoint(
    itinerary_id: int,
    place_id: int,
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Removes a place from an itinerary. User must be the owner of the itinerary.
    Service handles ownership and existence checks.
    """
    updated_itinerary = itinerary_service.remove_place_from_existing_itinerary(
        itinerary_id=itinerary_id, place_id=place_id, current_user=current_user
    )
    return updated_itinerary
