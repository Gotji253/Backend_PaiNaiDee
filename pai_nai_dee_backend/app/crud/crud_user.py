from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.password_utils import get_password_hash # Import from new location

class CRUDUser:
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create_user(self, db: Session, *, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password
            # interests=user_in.interests # If interests are part of UserCreate and User model
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update_user(self, db: Session, *, db_user: User, user_in: UserUpdate) -> User:
        update_data = user_in.model_dump(exclude_unset=True) # Pydantic V2

        if "password" in update_data and update_data["password"]: # Check if password is being updated
            hashed_password = get_password_hash(update_data["password"])
            db_user.hashed_password = hashed_password
            del update_data["password"] # Remove password from dict to avoid direct model field update

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def delete_user(self, db: Session, user_id: int) -> Optional[User]:
        user = db.query(User).get(user_id)
        if user:
            db.delete(user)
            db.commit()
        return user

user = CRUDUser()

# Note: The get_password_hash function needs to be implemented in app.core.security
# I will create a placeholder for app.core.security.py in this step if it's not already part of another step.
# Plan step 10 is "Implement Basic Authentication (core/security.py, api/endpoints/auth.py)"
# So, I will create a placeholder security.py now, and it will be fully implemented in step 10.
