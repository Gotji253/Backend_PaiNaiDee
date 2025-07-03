from pydantic import BaseModel, EmailStr
from typing import Optional  # List removed


# Shared properties
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    # interests: Optional[List[str]] = [] # Revisit if adding interests to user model


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None  # Allow password update


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int

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
