from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models
from .. import schemas # For schemas.PlaceCreate, schemas.PlaceUpdate
from fastapi import HTTPException, status

def get_place(db: Session, place_id: int) -> Optional[models.Place]:
    return db.query(models.Place).filter(models.Place.id == place_id).first()

def get_places(db: Session, skip: int = 0, limit: int = 100, category: Optional[str] = None, search_query: Optional[str] = None) -> List[models.Place]:
    query = db.query(models.Place)
    if category:
        query = query.filter(models.Place.category == category)
    if search_query:
        # Simple search in name and description. For more advanced search, consider dedicated search engines.
        query = query.filter(
            (models.Place.name.ilike(f"%{search_query}%")) |
            (models.Place.description.ilike(f"%{search_query}%"))
        )
    return query.offset(skip).limit(limit).all()

def create_place(db: Session, place: schemas.PlaceCreate) -> models.Place:
    # Optional: Check for duplicate place name/address if necessary
    # existing_place = db.query(models.Place).filter(models.Place.name == place.name, models.Place.address == place.address).first()
    # if existing_place:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Place with this name and address already exists")

    db_place = models.Place(**place.model_dump())
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

def update_place(db: Session, place_id: int, place_update: schemas.PlaceUpdate) -> Optional[models.Place]:
    db_place = get_place(db, place_id)
    if not db_place:
        return None # Or raise HTTPException

    update_data = place_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_place, field, value)

    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    return db_place

def delete_place(db: Session, place_id: int) -> Optional[models.Place]:
    db_place = get_place(db, place_id)
    if not db_place:
        return None # Or raise HTTPException

    # Consider what happens to reviews, activity logs for this place.
    # SQLAlchemy relationships with cascade delete might handle some of this,
    # or manual cleanup might be needed. For now, direct delete.
    # Example: db.query(models.Review).filter(models.Review.place_id == place_id).delete()

    db.delete(db_place)
    db.commit()
    return db_place
