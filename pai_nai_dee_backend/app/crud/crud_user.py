from sqlalchemy.orm import Session
from .. import models # Adjusted import path
from ..schemas import user as user_schema # Adjusted import path and aliased
from ..auth import jwt as auth_jwt # For password hashing, will create this file next

def get_user(db: Session, user_id: int):
    return db.query(models.user.User).filter(models.user.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.user.User).filter(models.user.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.user.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = auth_jwt.get_password_hash(user.password)
    db_user = models.user.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: user_schema.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True) # Use model_dump

    if "password" in update_data and update_data["password"]:
        hashed_password = auth_jwt.get_password_hash(update_data["password"])
        db_user.hashed_password = hashed_password

    for field, value in update_data.items():
        if field != "password": # Password already handled
            setattr(db_user, field, value)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if not db_user:
        return None # Or raise an exception
    db.delete(db_user)
    db.commit()
    return db_user
