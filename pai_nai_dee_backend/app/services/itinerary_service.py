from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app import crud, schemas
from app.models.itinerary import Itinerary as ItineraryModel
from app.models.user import User as UserModel
from app.services.place_service import PlaceService # To verify places


class ItineraryService:
    def __init__(self, db: Session):
        self.db = db
        self.place_service = PlaceService(db)

    def _validate_places_exist(self, place_ids: List[int]):
        """Helper to validate all place IDs exist."""
        if not place_ids:
            return
        for place_id in place_ids:
            # PlaceService.get_place_by_id will raise HTTPException if a place is not found
            self.place_service.get_place_by_id(place_id)

    def create_new_itinerary(self, itinerary_in: schemas.ItineraryCreate, current_user: UserModel) -> ItineraryModel:
        """
        Creates a new itinerary for the current user.
        Ensures all specified places exist.
        """
        if itinerary_in.place_ids:
            self._validate_places_exist(itinerary_in.place_ids)

        return crud.itinerary.create_itinerary(db=self.db, itinerary_in=itinerary_in, user_id=current_user.id)

    def get_itinerary_by_id_for_user(self, itinerary_id: int, current_user: UserModel) -> Optional[ItineraryModel]:
        """
        Retrieves a specific itinerary by ID.
        Ensures the current user is the owner or an admin.
        """
        itinerary = crud.itinerary.get_itinerary(self.db, itinerary_id=itinerary_id)
        if not itinerary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Itinerary not found",
            )
        if itinerary.user_id != current_user.id and current_user.role != schemas.UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to access this itinerary.",
            )
        return itinerary

    def get_all_itineraries_for_user(
        self, current_user: UserModel, skip: int = 0, limit: int = 20
    ) -> List[ItineraryModel]:
        """
        Retrieves all itineraries for the current authenticated user.
        If the user is an ADMIN, it could potentially retrieve all itineraries (not implemented here).
        """
        # if current_user.role == schemas.UserRole.ADMIN:
        #     return crud.itinerary.get_all_itineraries(self.db, skip=skip, limit=limit) # Requires get_all_itineraries in CRUD
        return crud.itinerary.get_itineraries_by_user(
            self.db, user_id=current_user.id, skip=skip, limit=limit
        )

    def update_existing_itinerary(
        self, itinerary_id: int, itinerary_in: schemas.ItineraryUpdate, current_user: UserModel
    ) -> Optional[ItineraryModel]:
        """
        Updates an existing itinerary. Ensures the user is the owner.
        Validates places if place_ids are being updated.
        """
        db_itinerary = self.get_itinerary_by_id_for_user(itinerary_id, current_user) # Handles 404 and ownership
        if not db_itinerary: # Should be caught by the above call
            return None

        if itinerary_in.place_ids is not None: # If place_ids is part of the update payload
            self._validate_places_exist(itinerary_in.place_ids)

        return crud.itinerary.update_itinerary(
            db=self.db, db_itinerary=db_itinerary, itinerary_in=itinerary_in
        )

    def delete_existing_itinerary(self, itinerary_id: int, current_user: UserModel) -> Optional[ItineraryModel]:
        """
        Deletes an itinerary. Ensures the user is the owner or an admin.
        """
        # get_itinerary_by_id_for_user already checks ownership/admin for viewing,
        # but delete might have stricter rules (e.g. only owner, or only admin but not owner via this path)
        # For now, if they can view it (owner/admin), they can attempt delete via service.
        db_itinerary = self.get_itinerary_by_id_for_user(itinerary_id, current_user)
        if not db_itinerary: # Should be caught
            return None

        return crud.itinerary.delete_itinerary(db=self.db, itinerary_id=itinerary_id)

    def add_place_to_existing_itinerary(
        self, itinerary_id: int, place_id: int, current_user: UserModel
    ) -> Optional[ItineraryModel]:
        """
        Adds a place to an existing itinerary. User must be the owner.
        """
        db_itinerary = self.get_itinerary_by_id_for_user(itinerary_id, current_user) # Handles 404 and ownership
        if not db_itinerary:
            return None

        # PlaceService.get_place_by_id will raise HTTPException if not found
        self.place_service.get_place_by_id(place_id)

        return crud.itinerary.add_place_to_itinerary(self.db, itinerary_id, place_id)

    def remove_place_from_existing_itinerary(
        self, itinerary_id: int, place_id: int, current_user: UserModel
    ) -> Optional[ItineraryModel]:
        """
        Removes a place from an existing itinerary. User must be the owner.
        """
        db_itinerary = self.get_itinerary_by_id_for_user(itinerary_id, current_user) # Handles 404 and ownership
        if not db_itinerary:
            return None

        # It's good practice to ensure the place exists before trying to remove it,
        # though the CRUD operation might handle it gracefully if the place isn't in the itinerary.
        # self.place_service.get_place_by_id(place_id) # Optional: check if place itself exists

        return crud.itinerary.remove_place_from_itinerary(self.db, itinerary_id, place_id)
