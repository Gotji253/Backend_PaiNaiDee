from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional # Removed Dict, Any for now as get_place_recommendations is a mock

from app import crud, schemas # Added schemas
from app.models.place import Place as PlaceModel # Added PlaceModel


class PlaceService:
    def __init__(self, db: Session):
        self.db = db

    def create_new_place(self, place_in: schemas.PlaceCreate) -> PlaceModel:
        """
        Creates a new place.
        Future enhancement: Check for duplicates based on name and address/location.
        """
        # Example duplicate check (optional, depends on business rules)
        # existing_place = self.db.query(PlaceModel)\
        # .filter(PlaceModel.name == place_in.name, PlaceModel.latitude == place_in.latitude, PlaceModel.longitude == place_in.longitude)\
        # .first()
        # if existing_place:
        #     raise HTTPException(
        #         status_code=status.HTTP_409_CONFLICT,
        #         detail="A place with this name and location already exists.",
        #     )
        return crud.place.create_place(db=self.db, place_in=place_in)

    def get_place_by_id(self, place_id: int) -> Optional[PlaceModel]:
        """
        Retrieves a place by its ID.
        """
        place = crud.place.get_place(self.db, place_id=place_id)
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place not found",
            )
        return place

    def get_all_places(
        self, skip: int = 0, limit: int = 100, category: Optional[str] = None, min_rating: Optional[float] = None
    ) -> List[PlaceModel]:
        """
        Retrieves a list of places, with optional filtering.
        """
        # More complex filtering logic could be added here if it involves more than direct DB queries
        return crud.place.get_places(
            db=self.db, skip=skip, limit=limit, category=category, min_rating=min_rating
        )

    def update_existing_place(self, place_id: int, place_in: schemas.PlaceUpdate) -> Optional[PlaceModel]:
        """
        Updates an existing place.
        """
        db_place = self.get_place_by_id(place_id) # Raises 404 if not found
        if not db_place: # Should be caught by get_place_by_id
            return None
        return crud.place.update_place(db=self.db, db_place=db_place, place_in=place_in)

    def delete_existing_place(self, place_id: int) -> Optional[PlaceModel]:
        """
        Deletes a place by its ID.
        """
        db_place = self.get_place_by_id(place_id) # Raises 404 if not found
        if not db_place: # Should be caught by get_place_by_id
            return None
        # Consider business logic: e.g., can a place with active reviews/itineraries be deleted?
        # If so, how to handle related entities (cascade, nullify, restrict).
        # For now, simple deletion.
        return crud.place.delete_place(db=self.db, place_id=place_id)

    def update_place_average_rating(self, place_id: int) -> Optional[PlaceModel]:
        """
        Calculates and updates the average rating for a place based on its reviews.
        Returns the updated place or None if not found.
        """
        place_model = crud.place.get_place(self.db, place_id=place_id)
        if not place_model:
            # Raising error here might be better if called internally and place must exist
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found for rating update")

        reviews = crud.review.get_reviews_by_place(self.db, place_id=place_id, limit=10000) # Get all reviews

        if not reviews:
            new_average_rating = 0.0
        else:
            new_average_rating = sum(r.rating for r in reviews) / len(reviews)

        place_model.average_rating = round(new_average_rating, 2) # Round to 2 decimal places
        self.db.add(place_model)
        self.db.commit()
        self.db.refresh(place_model)
        return place_model

    # def get_place_recommendations( ... ) remains as a placeholder for more complex logic
    def get_place_recommendations(
        self, user_id: int, top_n: int = 5
    ) -> List[schemas.Place]: # Changed to return List[schemas.Place] for consistency if mock is used
        """
        Placeholder for a recommendation engine.
        """
        # For now, mock by returning some highly-rated places
        # This would eventually use actual recommendation logic
        popular_places = crud.place.get_places(self.db, limit=top_n, min_rating=4.0)
        if not popular_places: # Mock if DB is empty or no high rated places
             return [
                schemas.Place(
                    id=i,
                    name=f"Highly Rated Mock Place {i}",
                    description="A great mock place",
                    category="Mock Category",
                    latitude=0.0,
                    longitude=0.0,
                    address=f"Mock Address {i}",
                    average_rating=round(4.0 + i / 10, 1) % 5 # Ensure rating is within 0-5
                )
                for i in range(1, top_n + 1)
            ]
        return popular_places
