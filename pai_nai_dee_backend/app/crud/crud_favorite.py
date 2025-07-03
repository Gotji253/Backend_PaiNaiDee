from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from .. import models
from ..schemas import place as place_schema # For returning list of Place objects

def add_favorite(db: Session, user_id: int, place_id: int) -> Optional[models.user.User]:
    user = db.query(models.user.User).filter(models.user.User.id == user_id).first()
    place = db.query(models.place.Place).filter(models.place.Place.id == place_id).first()

    if not user or not place:
        return None # User or Place not found

    if place not in user.favorite_places:
        user.favorite_places.append(place)
        db.commit()
        db.refresh(user) # Refresh user to reflect changes in relationships
    return user

def remove_favorite(db: Session, user_id: int, place_id: int) -> Optional[models.user.User]:
    user = db.query(models.user.User).filter(models.user.User.id == user_id).first()
    place = db.query(models.place.Place).filter(models.place.Place.id == place_id).first()

    if not user or not place:
        return None # User or Place not found

    if place in user.favorite_places:
        user.favorite_places.remove(place)
        db.commit()
        db.refresh(user)
    return user

def get_user_favorite_places(db: Session, user_id: int) -> Optional[List[models.place.Place]]:
    user = db.query(models.user.User).options(joinedload(models.user.User.favorite_places)).filter(models.user.User.id == user_id).first()
    if not user:
        return None # User not found
    return user.favorite_places # This will be a list of Place objects

def is_place_favorited_by_user(db: Session, user_id: int, place_id: int) -> bool:
    user = db.query(models.user.User).options(joinedload(models.user.User.favorite_places)).filter(models.user.User.id == user_id).first()
    if not user:
        return False # User not found, so can't be favorited

    for fav_place in user.favorite_places:
        if fav_place.id == place_id:
            return True
    return False
