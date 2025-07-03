from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None # 'sub' is standard for subject (user identifier)
    exp: Optional[int] = None # Expiry time
    # You can add other custom claims here if needed
    # e.g., roles: List[str] = []

class TokenData(BaseModel): # Kept for compatibility, but TokenPayload is more descriptive for JWT claims
    username: Optional[str] = None # This usually refers to the user's email or unique ID
    # id: Optional[int] = None # Alternative if 'sub' is not preferred for user ID storage directly
