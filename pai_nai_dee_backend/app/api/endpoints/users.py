from fastapi import APIRouter, Depends, HTTPException, status # Removed HTTPException as it's handled in service
from sqlalchemy.orm import Session
from typing import List, Any

from app import schemas
from app.db.database import get_db
from app.core.security import get_current_active_user, require_role # Added require_role
from app.schemas.user import UserRole # Added UserRole for RBAC
from app.models.user import User as UserModel
from app.services.user_service import UserService # Import UserService

router = APIRouter()


# Dependency to get UserService instance
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post(
    "/",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Creates a new user in the system. Currently open, but typically this would be admin-only or part of a registration flow."
)
def create_user(
    *,
    user_service: UserService = Depends(get_user_service),
    user_in: schemas.UserCreate,
    # current_user: UserModel = Depends(require_role([UserRole.ADMIN])) # Example: Only admins can create users
) -> Any:
    """
    Create new user.
    Open for now, but ideally, this should be protected (e.g., admin only or part of a public registration flow).
    """
    # Note: RBAC for user creation can be complex. Public registration vs admin creation.
    # For now, leaving it open and relying on service-layer validation for duplicates.
    user = user_service.create_new_user(user_in=user_in)
    return user


@router.get(
    "/",
    response_model=List[schemas.User],
    summary="Retrieve all users (Admin only)",
    description="Retrieves a list of all users. This endpoint is restricted to users with the ADMIN role."
)
def read_users(
    user_service: UserService = Depends(get_user_service),
    skip: int = 0,
    limit: int = 100,
    current_user: UserModel = Depends(require_role([UserRole.ADMIN])), # Only admins can list all users
) -> Any:
    """
    Retrieve users. (ADMINS ONLY)
    """
    users = user_service.get_all_users(skip=skip, limit=limit)
    return users


@router.get(
    "/{user_id}",
    response_model=schemas.User,
    summary="Get a specific user by ID",
    description="Retrieves information for a specific user by their ID. Users can retrieve their own information. Admins can retrieve any user's information."
)
def read_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    A user can get their own info, or an admin can get any user's info.
    """
    # Authorization: User can get themselves, or admin can get any.
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user's information.",
        )
    user = user_service.get_user_by_id(user_id=user_id)
    # Service method already raises HTTPException 404 if not found
    return user


@router.put(
    "/{user_id}",
    response_model=schemas.User,
    summary="Update a user",
    description="Updates a user's information. Users can update their own information. Admins can update any user's information, including their role. Non-admins cannot change their own role."
)
def update_user(
    *,
    user_id: int,
    user_in: schemas.UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Update a user.
    A user can update themselves, or an admin can update any user.
    """
    # Authorization: User can update themselves, or admin can update any.
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user.",
        )

    # Prevent non-admin users from changing their role
    if current_user.role != UserRole.ADMIN and user_in.role is not None and user_in.role != current_user.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Users cannot change their own role.",
        )

    # Admins should be able to set roles. If user_in.role is None, it won't be updated by Pydantic's exclude_unset.
    # If an admin is updating another user and doesn't provide 'role', it remains unchanged.
    # If an admin provides 'role', it will be updated by the service->crud layer.

    user = user_service.update_existing_user(user_id=user_id, user_in=user_in)
    # Service method handles 404 and conflict HTTPExceptions
    return user


@router.delete(
    "/{user_id}",
    response_model=schemas.User,
    summary="Delete a user (Admin only)",
    description="Deletes a user from the system. This endpoint is restricted to users with the ADMIN role."
)
def delete_user(
    *,
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: UserModel = Depends(require_role([UserRole.ADMIN])), # Example: Only admins can delete users
) -> Any:
    """
    Delete a user. (ADMINS ONLY - Specific RBAC applied)
    """
    # Further checks can be added here if needed, e.g., admin cannot delete themselves.
    # if current_user.id == user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admins cannot delete themselves through this endpoint.",
    #     )
    deleted_user = user_service.delete_existing_user(user_id=user_id)
    # Service method handles 404
    return deleted_user
