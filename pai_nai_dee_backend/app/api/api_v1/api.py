from fastapi import APIRouter

# Import endpoint modules here
from app.api.endpoints import users, places, reviews, itineraries, auth

router = APIRouter()

# Include routers from endpoint modules
router.include_router(
    auth.router, prefix="/auth", tags=["Authentication"]
)  # Added auth router
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(places.router, prefix="/places", tags=["Places"])
router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
router.include_router(itineraries.router, prefix="/itineraries", tags=["Itineraries"])


# Placeholder for root of v1, can be removed or expanded
@router.get("/", summary="API v1 Root", tags=["API Version 1"])
async def read_api_v1_root():
    """
    Welcome to API v1.
    """
    return {"message": "Welcome to Pai Nai Dee API v1"}
