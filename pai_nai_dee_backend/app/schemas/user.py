from pydantic import BaseModel, EmailStr
from typing import Optional


# Shared properties
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int

    class Config:
        from_attributes = True


# Additional properties to return to client
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
