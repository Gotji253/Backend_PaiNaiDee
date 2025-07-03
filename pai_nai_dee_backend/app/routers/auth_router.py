from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas # For Token schema
from .. import auth # For authentication logic and token generation
from ..services import users_service
from ..database import get_db

router = APIRouter(
    prefix="/api", # Consistent prefix for API endpoints
    tags=["authentication"],
)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    user = users_service.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate token using the helper from auth.py
    token_data = auth.generate_token_for_user(user_email=user.email, user_id=user.id, db=db)
    return token_data
