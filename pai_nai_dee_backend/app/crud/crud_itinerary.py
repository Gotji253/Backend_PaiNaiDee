from sqlalchemy.orm import Session
from typing import Optional, List

from ..models.itinerary import Itinerary
from ..models.place import Place  # Needed to fetch Place objects for association
from ..schemas.itinerary import ItineraryCreate, ItineraryUpdate


class CRUDItinerary:
    def get_itinerary(self, db: Session, itinerary_id: int) -> Optional[Itinerary]:
        return db.query(Itinerary).filter(Itinerary.id == itinerary_id).first()

    def get_itineraries_by_user(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 20
    ) -> List[Itinerary]:
        return (
            db.query(Itinerary)
            .filter(Itinerary.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_itinerary(
        self, db: Session, *, itinerary_in: ItineraryCreate, user_id: int
    ) -> Itinerary:
        db_itinerary = Itinerary(
            name=itinerary_in.name,
            description=itinerary_in.description,
            user_id=user_id,
        )

        # Handle places_ids to populate the many-to-many relationship
        if itinerary_in.place_ids:
            places = db.query(Place).filter(Place.id.in_(itinerary_in.place_ids)).all()
            db_itinerary.places_in_itinerary.extend(places)

        db.add(db_itinerary)
        db.commit()
        db.refresh(db_itinerary)
        return db_itinerary

    def update_itinerary(
        self, db: Session, *, db_itinerary: Itinerary, itinerary_in: ItineraryUpdate
    ) -> Itinerary:
        update_data = itinerary_in.model_dump(exclude_unset=True)

        if "place_ids" in update_data:
            place_ids = update_data.pop("place_ids")  # Handle place_ids separately
            if (
                place_ids is not None
            ):  # Check if it's None, meaning no change, or empty list to clear
                # Fetch Place objects for the new list of IDs
                places = db.query(Place).filter(Place.id.in_(place_ids)).all()
                db_itinerary.places_in_itinerary = (
                    places  # Replace existing places with the new list
                )
            # If place_ids is not in update_data, don't touch the places_in_itinerary relationship

        for field, value in update_data.items():
            setattr(db_itinerary, field, value)

        db.add(db_itinerary)
        db.commit()
        db.refresh(db_itinerary)
        return db_itinerary

    def delete_itinerary(self, db: Session, itinerary_id: int) -> Optional[Itinerary]:
        itinerary = db.query(Itinerary).get(itinerary_id)
        if itinerary:
            # Many-to-many associations are typically handled by SQLAlchemy if cascade is set,
            # or they might need to be cleared manually if not using cascade delete-orphan on the relationship items.
            # For itinerary_place_association, default cascade behavior on the association proxy
            # usually means deleting the Itinerary will remove its entries from the association table.
            db.delete(itinerary)
            db.commit()
        return itinerary

    # Helper methods for managing places in an itinerary (optional additions)
    def add_place_to_itinerary(
        self, db: Session, itinerary_id: int, place_id: int
    ) -> Optional[Itinerary]:
        itinerary = self.get_itinerary(db, itinerary_id)
        place = db.query(Place).get(place_id)
        if itinerary and place:
            if place not in itinerary.places_in_itinerary:
                itinerary.places_in_itinerary.append(place)
                db.commit()
                db.refresh(itinerary)
            return itinerary
        return None

    def remove_place_from_itinerary(
        self, db: Session, itinerary_id: int, place_id: int
    ) -> Optional[Itinerary]:
        itinerary = self.get_itinerary(db, itinerary_id)
        place = db.query(Place).get(place_id)
        if itinerary and place:
            if place in itinerary.places_in_itinerary:
                itinerary.places_in_itinerary.remove(place)
                db.commit()
                db.refresh(itinerary)
            return itinerary
        return None


itinerary = CRUDItinerary()
