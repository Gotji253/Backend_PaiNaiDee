from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app import schemas  # Updated import
from app import crud  # Updated import
from app.db.database import get_db
from app.models.user import User as UserModel
from app.core.security import get_current_active_user  # Using actual dependency

router = APIRouter()


@router.post("/", response_model=schemas.Itinerary, status_code=status.HTTP_201_CREATED)
def create_itinerary(
    *,
    db: Session = Depends(get_db),
    itinerary_in: schemas.ItineraryCreate,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Create new itinerary for the current authenticated user.
    """
    # Check if all place_ids exist
    if itinerary_in.place_ids:
        for place_id in itinerary_in.place_ids:
            place = crud.crud_place.get_place(db, place_id=place_id)
            if not place:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place with id {place_id} not found.",
                )

    itinerary = crud.crud_itinerary.create_itinerary(
        db=db, itinerary_in=itinerary_in, user_id=current_user.id
    )
    return itinerary


@router.get("/my-itineraries", response_model=List[schemas.Itinerary])
def read_my_itineraries(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Get all itineraries for the current authenticated user.
    """
    itineraries = crud.crud_itinerary.get_itineraries_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return itineraries


@router.get("/{itinerary_id}", response_model=schemas.Itinerary)
def read_itinerary_by_id(
    itinerary_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(
        get_current_active_user
    ),  # Requires auth for permission check
) -> Any:
    """
    Get a specific itinerary by id. User must be the owner.
    (Admins could have broader access - to be implemented).
    """
    itinerary = crud.crud_itinerary.get_itinerary(db, itinerary_id=itinerary_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
        )

    if (
        itinerary.user_id != current_user.id
    ):  # and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    return itinerary


@router.put("/{itinerary_id}", response_model=schemas.Itinerary)
def update_itinerary(
    *,
    db: Session = Depends(get_db),
    itinerary_id: int,
    itinerary_in: schemas.ItineraryUpdate,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Update an itinerary. User must be the owner.
    """
    db_itinerary = crud.crud_itinerary.get_itinerary(db, itinerary_id=itinerary_id)
    if not db_itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
        )

    if (
        db_itinerary.user_id != current_user.id
    ):  # and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    # Check if all place_ids in the update exist (if provided)
    if itinerary_in.place_ids is not None:  # Check if place_ids is part of the update
        for place_id in itinerary_in.place_ids:
            place = crud.crud_place.get_place(db, place_id=place_id)
            if not place:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place with id {place_id} not found in update payload.",
                )

    itinerary = crud.crud_itinerary.update_itinerary(
        db=db, db_itinerary=db_itinerary, itinerary_in=itinerary_in
    )
    return itinerary


@router.delete("/{itinerary_id}", response_model=schemas.Itinerary)
def delete_itinerary(
    *,
    db: Session = Depends(get_db),
    itinerary_id: int,
    current_user: UserModel = Depends(get_current_active_user),  # Requires auth
) -> Any:
    """
    Delete an itinerary. User must be the owner.
    """
    db_itinerary = crud.crud_itinerary.get_itinerary(db, itinerary_id=itinerary_id)
    if not db_itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found"
        )

    if (
        db_itinerary.user_id != current_user.id
    ):  # and not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    deleted_itinerary = crud.crud_itinerary.delete_itinerary(
        db=db, itinerary_id=itinerary_id
    )
    if not deleted_itinerary:  # Should not happen
        raise HTTPException(
            status_code=404, detail="Itinerary not found during delete operation"
        )
    return deleted_itinerary


# Optional: Endpoints to manage places within an itinerary
@router.post("/{itinerary_id}/places/{place_id}", response_model=schemas.Itinerary)
def add_place_to_itinerary_endpoint(
    itinerary_id: int,
    place_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    itinerary = crud.crud_itinerary.get_itinerary(db, itinerary_id=itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    if itinerary.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    place = crud.crud_place.get_place(db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    updated_itinerary = crud.crud_itinerary.add_place_to_itinerary(
        db, itinerary_id, place_id
    )
    if not updated_itinerary:  # Should not happen if checks above pass
        raise HTTPException(status_code=500, detail="Could not add place to itinerary")
    return updated_itinerary


@router.delete("/{itinerary_id}/places/{place_id}", response_model=schemas.Itinerary)
def remove_place_from_itinerary_endpoint(
    itinerary_id: int,
    place_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    itinerary = crud.crud_itinerary.get_itinerary(db, itinerary_id=itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    if itinerary.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    place = crud.crud_place.get_place(db, place_id=place_id)
    if (
        not place
    ):  # Technically, crud.remove_place_from_itinerary handles this, but good to check early.
        raise HTTPException(status_code=404, detail="Place not found to remove")

    updated_itinerary = crud.crud_itinerary.remove_place_from_itinerary(
        db, itinerary_id, place_id
    )
    if not updated_itinerary:  # This might happen if place was not in itinerary.
        # We could return 200 OK with the itinerary as is, or 404 if place wasn't part of it.
        # The CRUD returns the itinerary even if place wasn't there.
        # For consistency, let's ensure it's not None (which means itinerary itself wasn't found by CRUD)
        raise HTTPException(
            status_code=500, detail="Could not remove place from itinerary"
        )
    return updated_itinerary
