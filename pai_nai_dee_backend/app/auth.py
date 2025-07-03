from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

# Pydantic models Token and TokenData moved to schemas.auth_schemas
from .schemas.auth_schemas import Token, TokenData
from .services import users_service
from .models.users import User as UserModel
from .database import get_db
from sqlalchemy.orm import Session

# Configuration
SECRET_KEY = "your-secret-key-please-change-in-production" # TODO: Move to env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token") # Matches the token endpoint

# class Token(BaseModel): # Moved to schemas.auth_schemas
#     access_token: str
#     token_type: str

# class TokenData(BaseModel): # Moved to schemas.auth_schemas
#     username: Optional[str] = None
#     user_id: Optional[int] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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
        username: Optional[str] = payload.get("sub") # "sub" is standard for subject (username/email)
        user_id: Optional[int] = payload.get("id")

        if username is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(username=username, user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = users_service.get_user(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# (Optional) Dependency for superuser
# async def get_current_active_superuser(
#     current_user: UserModel = Depends(get_current_active_user),
# ) -> UserModel:
#     if not current_user.is_superuser:
#         raise HTTPException(
#             status_code=403, detail="The user doesn't have enough privileges"
#         )
#     return current_user

# Token generation endpoint logic (to be used in a router)
def generate_token_for_user(user_email: str, user_id: int, db: Session) -> Token:
    # This function is a helper, the actual authentication against password
    # should happen before calling this (e.g. in a /token endpoint).

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_email, "id": user_id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
