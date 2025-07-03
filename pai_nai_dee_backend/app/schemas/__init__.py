# This file makes the 'schemas' directory a Python package.
# Schemas (Pydantic models) will be defined in separate files within this package.

from .places import Place, PlaceCreate, PlaceUpdate, PlaceBase, PlaceRecommendation
from .recommendations import RecommendationResponse
from .reviews import Review, ReviewCreate, ReviewUpdate, ReviewBase
from .users import User, UserCreate, UserUpdate, UserBase, UserInDB, UserInDBBase
from .auth_schemas import Token, TokenData
# Add other schemas as they are created, e.g.:
