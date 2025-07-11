from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from ...schemas import User as UserSchema, UserCreate, UserUpdate
from ...crud import crud_user
from ...db.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User as UserModel

router = APIRouter()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud_user.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this username already exists in the system.",
        )
    if user_in.email:
        user_by_email = crud_user.get_user_by_email(db, email=user_in.email)
        if user_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )

    user = crud_user.create_user(db=db, user_in=user_in)
    return user


@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(
        get_current_active_user
    ),  # To protect this endpoint
) -> Any:
    """
    Retrieve users. (ADMINS ONLY - TODO: Implement proper role check)
    """
    # Example of a superuser check (assuming is_superuser is a method in crud_user or a model property)
    # if not crud_user.is_superuser(current_user):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    # For now, any authenticated user can access this. This needs to be locked down.
    users = crud_user.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),  # For authorization
) -> Any:
    """
    Get a specific user by id. (User can get themselves, or admin can get any)
    """
    user = crud_user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    # if user != current_user and not crud_user.is_superuser(current_user): # Example check
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),  # For authorization
) -> Any:
    """
    Update a user. (User can update themselves, or admin can update any)
    """
    db_user = crud_user.get_user(db, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this id does not exist in the system",
        )
    # if db_user != current_user and not crud_user.is_superuser(current_user): # Example check
    #    raise HTTPException(status_code=403, detail="Not enough permissions")

    # Check for email conflict if email is being updated
    if user_in.email and db_user.email != user_in.email:
        existing_user = crud_user.get_user_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another user with this email already exists.",
            )

    # Check for username conflict if username is being updated
    if user_in.username and db_user.username != user_in.username:
        existing_user = crud_user.get_user_by_username(
            db, username=user_in.username
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another user with this username already exists.",
            )

    user = crud_user.update_user(db=db, db_user=db_user, user_in=user_in)
    return user


@router.delete("/{user_id}", response_model=UserSchema)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),  # For authorization
) -> Any:
    """
    Delete a user. (ADMINS ONLY - TODO: Implement proper role check, or user can delete self)
    """
    user_to_delete = crud_user.get_user(db, user_id=user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    # Add permission checks here, e.g., only admin or the user themselves can delete
    # if user_to_delete.id != current_user.id and not crud_user.is_superuser(current_user):
    #     raise HTTPException(status_code=403, detail="Not enough permissions to delete this user")

    deleted_user = crud_user.delete_user(db=db, user_id=user_id)
    if (
        not deleted_user
    ):  # Should not happen if previous check passed, but as a safeguard
        raise HTTPException(
            status_code=404, detail="User not found during delete operation"
        )
    return deleted_user
