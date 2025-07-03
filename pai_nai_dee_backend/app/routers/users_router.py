from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services import users_service
from .. import schemas # Access as schemas.User, schemas.UserCreate etc.
from ..models.users import User as UserModel
from ..auth import get_current_active_user # Import the real dependency

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
    # current_user: UserModel = Depends(get_current_active_user) # Optional: Protect user creation
):
    # Anyone can create a user for now (typical registration)
    db_user = users_service.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = users_service.create_user(db=db, user=user)
    return created_user

@router.get("/", response_model=List[schemas.User])
def read_users_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect this list
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    users = users_service.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect access
):
    if not (current_user.is_superuser or current_user.id == user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    db_user = users_service.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user_endpoint(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect update
):
    if not (current_user.is_superuser or current_user.id == user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to update this user")

    updated_user = users_service.update_user(db, user_id=user_id, user_update=user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}", response_model=schemas.User)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user) # Protect deletion
):
    if not current_user.is_superuser: # Only superuser can delete users for now
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to delete user")

    deleted_user = users_service.delete_user(db, user_id=user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user
