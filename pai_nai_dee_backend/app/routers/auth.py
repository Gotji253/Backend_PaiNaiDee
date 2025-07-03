from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud # Adjusted import
from .. import schemas # Adjusted import
from .. import models # Adjusted import
from ..auth import jwt as jwt_utils # Adjusted import
from ..auth.dependencies import get_current_active_user # Adjusted import
from ..database import get_db # Adjusted import
from ..core.config import settings

router = APIRouter()

@router.post("/login", response_model=schemas.token.Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    # form_data.username is the email in this case
    user = crud.user.get_user_by_email(db, email=form_data.username)
    if not user or not jwt_utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt_utils.create_access_token(
        subject=user.email, expires_delta=access_token_expires # Using email as subject
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=schemas.user.User)
async def register_user(
    user_in: schemas.user.UserCreate,
    db: Session = Depends(get_db)
):
    db_user = crud.user.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    new_user = crud.user.create_user(db=db, user=user_in)
    return new_user

@router.get("/users/me", response_model=schemas.user.User)
async def read_users_me(
    current_user: models.user.User = Depends(get_current_active_user) # Using SQLAlchemy model from dependency
):
    # The dependency already returns the user model instance
    return current_user

# Example of a protected route that requires an active user
@router.get("/users/me/items") # Just an example endpoint
async def read_own_items(
    current_user: models.user.User = Depends(get_current_active_user)
):
    return [{"item_id": "Foo", "owner": current_user.email}]
