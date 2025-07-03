from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from . import jwt as jwt_utils # Renamed to avoid conflict
from .. import crud # Adjusted import to top-level crud
from .. import models # Adjusted import to top-level models
from .. import schemas # Adjusted import to top-level schemas
from ..database import get_db # Adjusted import path
from ..core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login") # Adjusted tokenUrl to match future router

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> models.user.User: # Return SQLAlchemy model instance
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt_utils.decode_token(token)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Assuming 'sub' in JWT contains the user's email
        # If it contains user_id, adjust crud.user.get_user_by_email to crud.user.get_user
        # token_data = schemas.token.TokenData(username=username) # Or TokenPayload if using that for 'sub'
        user_identifier = username # Assuming 'sub' is email, if it's ID, convert to int

    except JWTError:
        raise credentials_exception

    # Try to get user by email first (if 'sub' is email)
    user = crud.user.get_user_by_email(db, email=user_identifier)
    if user is None:
        # If 'sub' could be an ID, try by ID as a fallback or primary method
        # try:
        #     user_id = int(user_identifier)
        #     user = crud.user.get_user(db, user_id=user_id)
        # except ValueError:
        #     pass # Not an integer ID
        # if user is None:
        raise credentials_exception # User not found by email or ID

    return user

async def get_current_active_user(
    current_user: models.user.User = Depends(get_current_user) # Return SQLAlchemy model
) -> models.user.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# Dependency for superuser (optional, example)
# async def get_current_active_superuser(
#     current_user: models.user.User = Depends(get_current_active_user),
# ) -> models.user.User:
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
#         )
#     return current_user
