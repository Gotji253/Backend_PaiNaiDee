from fastapi import APIRouter

from app.api import auth, places, trips  # Import your route modules here
from app.core.config import settings

# This main API router will include routers from auth, places, trips, etc.
# It will be prefixed with settings.API_V1_STR in main.py
api_router = APIRouter()

# Include the auth router
# The prefix and tags help organize the API documentation (Swagger UI)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(places.router, prefix="/places", tags=["Places"])
api_router.include_router(
    trips.router, prefix="/trips", tags=["Trips"]
)  # Added Trips router
# Note: The overall prefix /api/v1 will be added when this api_router is included in the main app.
# So the auth routes will be /api/v1/auth/login etc.
# And places routes will be /api/v1/places/ etc.
# And trips routes will be /api/v1/trips/ etc.

# Future routers will be added here:
# from app.api import reviews
# api_router.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
