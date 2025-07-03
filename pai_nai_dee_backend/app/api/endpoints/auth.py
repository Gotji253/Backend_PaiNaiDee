from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app import crud
from app import schemas
from app.db.database import get_db
from app.core.security import create_access_token  #  verify_password removed from here
from app.core.password_utils import verify_password  #  Import directly
from app.core.config import settings
from app.models.user import User as UserModel  #  For type hinting current_user
from app.core.security import get_current_active_user  #  Import the actual dependency

router = APIRouter()


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud.crud_user.get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Add is_active check if implemented on user model
    # if not user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: UserModel = Depends(get_current_active_user)):
    """
    Test access token.
    """
    return current_user
