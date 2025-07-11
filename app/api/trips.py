from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.post("/", response_model=schemas.Trip, status_code=status.HTTP_201_CREATED)
def create_trip(
    *,
    db: Session = Depends(get_db),
    trip_in: schemas.TripCreate,  # owner_id is in TripCreate but we'll use current_user.id
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create a new trip for the current authenticated user.
    The `owner_id` from `trip_in` will be ignored and replaced by `current_user.id`.
    """
    # Ensure trip_in.owner_id is not used, or validate if it matches current_user.id
    # For simplicity, we directly use current_user.id in the CRUD operation
    trip_create_internal = schemas.TripCreate(
        **trip_in.model_dump(exclude={"owner_id"})
    )

    trip = crud.trip.create_with_owner(
        db=db, obj_in=trip_create_internal, owner_id=current_user.id
    )
    return trip


@router.get("/", response_model=List[schemas.Trip])
def read_trips(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve trips for the current authenticated user.
    Admins could potentially see all trips by modifying this or adding another endpoint.
    """
    # if crud.user.is_superuser(current_user):
    #     trips = crud.trip.get_multi(db, skip=skip, limit=limit)
    # else:
    trips = crud.trip.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return trips


@router.get("/{trip_id}", response_model=schemas.Trip)
def read_trip(
    *,
    db: Session = Depends(get_db),
    trip_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get a specific trip by ID, owned by the current authenticated user.
    """
    trip = crud.trip.get(db=db, id=trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.owner_id != current_user.id and not crud.user.is_superuser(
        current_user
    ):  # Allow superuser to access any trip
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    return trip


@router.put("/{trip_id}", response_model=schemas.Trip)
def update_trip(
    *,
    db: Session = Depends(get_db),
    trip_id: int,
    trip_in: schemas.TripUpdate,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update a trip owned by the current authenticated user.
    """
    trip = crud.trip.get(db=db, id=trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.owner_id != current_user.id and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this trip",
        )

    # If owner_id is part of TripUpdate and is being changed, add specific permission check
    if trip_in.owner_id is not None and trip_in.owner_id != trip.owner_id:
        if not crud.user.is_superuser(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can change trip ownership.",
            )

    trip = crud.trip.update(db=db, db_obj=trip, obj_in=trip_in)
    return trip


@router.delete(
    "/{trip_id}", response_model=schemas.Trip
)  # Consider returning 204 No Content
def delete_trip(
    *,
    db: Session = Depends(get_db),
    trip_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete a trip owned by the current authenticated user.
    """
    trip = crud.trip.get(db=db, id=trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.owner_id != current_user.id and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this trip",
        )

    deleted_trip = crud.trip.remove(db=db, id=trip_id)
    return deleted_trip


# --- Routes for managing places within a trip ---


@router.post("/{trip_id}/places/{place_id}", response_model=schemas.Trip)
def add_place_to_trip_route(
    *,
    db: Session = Depends(get_db),
    trip_id: int,
    place_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Add a place to a specific trip.
    """
    trip = crud.trip.get(db=db, id=trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.owner_id != current_user.id and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for this trip",
        )

    place = crud.place.get(db=db, id=place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
        )

    trip = crud.trip.add_place_to_trip(db=db, trip=trip, place=place)
    return trip


@router.delete("/{trip_id}/places/{place_id}", response_model=schemas.Trip)
def remove_place_from_trip_route(
    *,
    db: Session = Depends(get_db),
    trip_id: int,
    place_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Remove a place from a specific trip.
    """
    trip = crud.trip.get(db=db, id=trip_id)
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.owner_id != current_user.id and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions for this trip",
        )

    place = crud.place.get(db=db, id=place_id)
    if not place:
        # Technically, if place doesn't exist, it can't be in the trip.
        # Depending on desired behavior, could return 404 for place or proceed.
        # If proceeding, crud.trip.remove_place_from_trip should handle place not in trip.places gracefully.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Place not found"
        )

    trip = crud.trip.remove_place_from_trip(db=db, trip=trip, place=place)
    return trip
