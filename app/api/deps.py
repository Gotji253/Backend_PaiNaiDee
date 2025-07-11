from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core import security  # For verify_token
from app import crud, models  # For user model and crud operations
from app.db.session import SessionLocal, get_db  # For get_db
from app.schemas.token import TokenPayload  # For token payload schema

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user_from_token(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValueError):  # ValueError for Pydantic validation error
        raise credentials_exception

    if token_data.sub is None:  # Check if 'sub' (subject, e.g. email) is in token
        raise credentials_exception

    user = crud.user.get_by_email(db, email=token_data.sub)
    if not user:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user_from_token),
) -> models.User:
    if not crud.user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


def get_current_active_superuser(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if not crud.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user
