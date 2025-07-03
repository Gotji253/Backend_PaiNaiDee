from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.place import Place
from app.schemas.place import PlaceCreate, PlaceUpdate

class CRUDPlace:
    def get_place(self, db: Session, place_id: int) -> Optional[Place]:
        return db.query(Place).filter(Place.id == place_id).first()

    def get_places(
        self, db: Session, skip: int = 0, limit: int = 100,
        category: Optional[str] = None, min_rating: Optional[float] = None
    ) -> List[Place]:
        query = db.query(Place)
        if category:
            query = query.filter(Place.category.ilike(f"%{category}%")) # Case-insensitive search
        if min_rating is not None: # Ensure min_rating can be 0.0
            query = query.filter(Place.average_rating >= min_rating)
        return query.offset(skip).limit(limit).all()

    def create_place(self, db: Session, *, place_in: PlaceCreate) -> Place:
        db_place = Place(
            name=place_in.name,
            description=place_in.description,
            category=place_in.category,
            latitude=place_in.latitude,
            longitude=place_in.longitude,
            address=place_in.address
            # average_rating is not set on creation, defaults to 0.0 or handled by a trigger/service
        )
        db.add(db_place)
        db.commit()
        db.refresh(db_place)
        return db_place

    def update_place(self, db: Session, *, db_place: Place, place_in: PlaceUpdate) -> Place:
        update_data = place_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_place, field, value)

        # average_rating updates would typically be handled by a separate mechanism
        # e.g., when a new review is added.

        db.add(db_place)
        db.commit()
        db.refresh(db_place)
        return db_place

    def delete_place(self, db: Session, place_id: int) -> Optional[Place]:
        place = db.query(Place).get(place_id)
        if place:
            db.delete(place)
            db.commit()
        return place

    # Future: update_place_rating (e.g. called when a review is added/updated/deleted)
    # def update_place_average_rating(self, db: Session, place_id: int) -> Place:
    #     place = self.get_place(db, place_id)
    #     if not place:
    #         # Handle error or return None
    #         return None
    #     # Calculate average from place.reviews
    #     if place.reviews:
    #         new_avg_rating = sum(r.rating for r in place.reviews) / len(place.reviews)
    #         place.average_rating = new_avg_rating
    #     else:
    #         place.average_rating = 0.0
    #     db.add(place)
    #     db.commit()
    #     db.refresh(place)
    #     return place


place = CRUDPlace()
