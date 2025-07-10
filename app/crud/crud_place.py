from sqlalchemy.orm import Session
from typing import List, Optional

from app.crud.base import CRUDBase
from app.models.place import Place
from app.schemas.place import PlaceCreate, PlaceUpdate

class CRUDPlace(CRUDBase[Place, PlaceCreate, PlaceUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Place]:
        return db.query(Place).filter(Place.name == name).first()

    # Additional CRUD methods specific to Place can be added here
    # For example, searching by category, location, etc.
    def get_multi_by_category(
        self, db: Session, *, category: str, skip: int = 0, limit: int = 100
    ) -> List[Place]:
        return (
            db.query(self.model)
            .filter(Place.category == category)
            .offset(skip)
            .limit(limit)
            .all()
        )

place = CRUDPlace(Place)
