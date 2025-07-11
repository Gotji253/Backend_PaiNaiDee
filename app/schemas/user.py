from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    is_active: Optional[bool] = True
    # is_superuser: bool = False # Not typically set by user on creation
    # full_name: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    id: int
    # Add model_config = ConfigDict(from_attributes=True) to allow ORM mode
    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
