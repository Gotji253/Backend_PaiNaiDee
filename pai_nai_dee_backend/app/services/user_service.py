from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app import crud, schemas
from app.models.user import User as UserModel


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def create_new_user(self, user_in: schemas.UserCreate) -> UserModel:
        """
        Creates a new user after validating username and email uniqueness.
        """
        existing_user_by_username = crud.user.get_user_by_username(self.db, username=user_in.username)
        if existing_user_by_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this username already exists in the system.",
            )
        if user_in.email:
            existing_user_by_email = crud.user.get_user_by_email(self.db, email=user_in.email)
            if existing_user_by_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The user with this email already exists in the system.",
                )

        user = crud.user.create_user(db=self.db, user_in=user_in)
        return user

    def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        """
        Retrieves a user by their ID.
        """
        user = crud.user.get_user(self.db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The user with this id does not exist in the system.",
            )
        return user

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """
        Retrieves a list of users.
        """
        users = crud.user.get_users(self.db, skip=skip, limit=limit)
        return users

    def update_existing_user(self, user_id: int, user_in: schemas.UserUpdate) -> Optional[UserModel]:
        """
        Updates an existing user's information.
        Handles username and email conflict checks.
        """
        db_user = self.get_user_by_id(user_id) # This will raise 404 if not found
        if not db_user: # Should be caught by get_user_by_id, but defensive
            return None

        # Check for email conflict if email is being updated
        if user_in.email and db_user.email != user_in.email:
            existing_user_by_email = crud.user.get_user_by_email(self.db, email=user_in.email)
            if existing_user_by_email and existing_user_by_email.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another user with this email already exists.",
                )

        # Check for username conflict if username is being updated
        if user_in.username and db_user.username != user_in.username:
            existing_user_by_username = crud.user.get_user_by_username(
                self.db, username=user_in.username
            )
            if existing_user_by_username and existing_user_by_username.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another user with this username already exists.",
                )

        updated_user = crud.user.update_user(db=self.db, db_user=db_user, user_in=user_in)
        return updated_user

    def delete_existing_user(self, user_id: int) -> Optional[UserModel]:
        """
        Deletes a user by their ID.
        """
        user_to_delete = self.get_user_by_id(user_id) # This will raise 404 if not found
        if not user_to_delete: # Should be caught by get_user_by_id
            return None

        deleted_user = crud.user.delete_user(db=self.db, user_id=user_id)
        # crud.user.delete_user already returns the user or None if not found after trying to get it.
        # The self.get_user_by_id ensures it exists before calling crud.delete.
        return deleted_user

# It's common to instantiate services directly in the endpoint handlers
# by passing the db session, rather than making the service itself a complex dependency.
# So, the get_user_service factory might not be needed if we follow that pattern.
