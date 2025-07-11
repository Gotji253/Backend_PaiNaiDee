from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from typing import List # Added List

# Pydantic BaseModel might not be needed here anymore if TokenData is the only schema used from app.schemas
# from pydantic import BaseModel

from app.core.config import settings
# verify_password removed, will be imported directly where needed from password_utils
from app.db.database import get_db
from app.schemas import TokenData # Corrected import (app.schemas.token.TokenData)
from app.schemas.user import UserRole # Added UserRole for RBAC
from app.crud import crud_user  # Corrected import (app.crud.crud_user)
from app.models.user import User as UserModel


ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# verify_password is imported from .password_utils


# JWT Token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# OAuth2PasswordBearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        # Ensure TokenData can be instantiated with username if that's its only field
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    if token_data.username is None:  #  Should be caught by payload.get("sub") check, but defensive
        raise credentials_exception

    user = crud_user.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    # Example check for active user (if 'is_active' field exists on UserModel)
    # if not current_user.is_active:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


# RBAC Dependency
def require_role(allowed_roles: List[UserRole]):
    """
    Dependency that checks if the current user has one of the allowed roles.
    """

    async def role_checker(
        current_user: UserModel = Depends(get_current_active_user),
    ) -> UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required role. Allowed roles: {', '.join([role.value for role in allowed_roles])}",
            )
        return current_user

    return role_checker


# Example for checking if a user is an admin - can be used directly in path operations
# require_admin_role = require_role([UserRole.ADMIN])

# Optional: For superuser checks (if roles/superuser status is implemented)
# async def get_current_active_superuser(
#     current_user: UserModel = Depends(get_current_active_user),
# ) -> UserModel:
#     if not crud_user.is_superuser(current_user): # Requires is_superuser method/property
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
#         )
#     return current_user
