from pydantic import BaseModel, EmailStr, constr, PositiveInt
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    USER = "user"


# Shared properties
class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: UserRole = UserRole.USER # Default role is USER
    # interests: Optional[List[str]] = [] # Revisit if adding interests to user model


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: constr(min_length=8)


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[constr(min_length=8)] = None  # Allow password update


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: PositiveInt

    class Config:
        # This used to be orm_mode = True
        # For Pydantic V2, it's from_attributes = True
        from_attributes = True


# Additional properties to return to client
class User(UserInDBBase):
    pass  # No extra fields for now, but can add related data here if needed


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
