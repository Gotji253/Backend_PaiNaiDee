from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any

from app.crud.base import CRUDBase
from app.models.trip import Trip
from app.models.place import Place # Needed to fetch Place objects
from app.schemas.trip import TripCreate, TripUpdate

class CRUDTrip(CRUDBase[Trip, TripCreate, TripUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: TripCreate, owner_id: int
    ) -> Trip:
        db_obj = Trip(
            name=obj_in.name,
            description=obj_in.description,
            start_date=obj_in.start_date,
            end_date=obj_in.end_date,
            owner_id=owner_id # Set owner_id from the authenticated user
        )

        # Handle places association
        if obj_in.place_ids:
            places = db.query(Place).filter(Place.id.in_(obj_in.place_ids)).all()
            db_obj.places.extend(places)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Trip]:
        return (
            db.query(self.model)
            .filter(Trip.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(
        self, db: Session, *, db_obj: Trip, obj_in: Union[TripUpdate, Dict[str, Any]]
    ) -> Trip:
        # Convert Pydantic model to dict if necessary, excluding unset values
        if isinstance(obj_in, TripUpdate):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = obj_in

        # Handle places association update
        if "place_ids" in update_data:
            place_ids = update_data.pop("place_ids") # Remove from update_data before super().update
            if place_ids is not None: # If place_ids is explicitly provided (even if empty list)
                # Fetch Place objects from IDs
                places = db.query(Place).filter(Place.id.in_(place_ids)).all()
                db_obj.places = places # Replace existing places with the new list
            # If place_ids is not in update_data, places are not touched by this part
            # If place_ids is None (explicitly set to None in request), it will be handled by ORM if field is nullable or cleared.
            # Here, we assume if place_ids is in the payload, it's the definitive list.

        # Use the parent class's update method for other fields
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    # You can add methods like add_place_to_trip, remove_place_from_trip if needed
    # For example:
    def add_place_to_trip(self, db: Session, *, trip: Trip, place: Place) -> Trip:
        if place not in trip.places:
            trip.places.append(place)
            db.add(trip)
            db.commit()
            db.refresh(trip)
        return trip

    def remove_place_from_trip(self, db: Session, *, trip: Trip, place: Place) -> Trip:
        if place in trip.places:
            trip.places.remove(place)
            db.add(trip)
            db.commit()
            db.refresh(trip)
        return trip

trip = CRUDTrip(Trip)
