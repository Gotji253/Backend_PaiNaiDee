from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models # Adjusted import
from ..schemas import place as place_schema # Adjusted import and aliased

def get_place(db: Session, place_id: int) -> Optional[models.place.Place]:
    return db.query(models.place.Place).filter(models.place.Place.id == place_id).first()

def get_places(
    db: Session, skip: int = 0, limit: int = 100, category: Optional[str] = None
) -> List[models.place.Place]:
    query = db.query(models.place.Place)
    if category:
        query = query.filter(models.place.Place.category == category)
    return query.offset(skip).limit(limit).all()

def create_place(db: Session, place: place_schema.PlaceCreate) -> models.place.Place:
    # If you add submitter_id, it should be passed in or handled here
    # db_place = models.place.Place(**place.model_dump(), submitter_id=current_user_id)
    db_place = models.place.Place(**place.model_dump())
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

def update_place(
    db: Session, place_id: int, place_update: place_schema.PlaceUpdate
) -> Optional[models.place.Place]:
    db_place = get_place(db, place_id)
    if not db_place:
        return None

    update_data = place_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_place, field, value)

    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

def delete_place(db: Session, place_id: int) -> Optional[models.place.Place]:
    db_place = get_place(db, place_id)
    if not db_place:
        return None
    db.delete(db_place)
    db.commit()
    # After deletion, the db_place object is no longer valid for refresh.
    # Return it as is, or just a confirmation. For consistency, returning the object.
    return db_place
