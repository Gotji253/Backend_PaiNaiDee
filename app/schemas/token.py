from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None  # Subject of the token (e.g., user_id or email)
    # We can add more fields here like scopes, etc. if needed in the future.
    # exp: Optional[int] = None # Expiry is handled by JWT itself but can be included if desired from payload
    # iat: Optional[int] = None # Issued at
    # iss: Optional[str] = None # Issuer
    # aud: Optional[str] = None # Audience
