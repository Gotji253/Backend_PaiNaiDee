from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services import recommendations as recommendation_service
from ..schemas.recommendations import RecommendationResponse
from ..schemas.places import Place as PlaceSchema # Renaming to avoid conflict with models.Place
from ..models.users import User as UserModel
from ..auth import get_current_active_user # Import the real dependency

router = APIRouter(
    prefix="/api/recommendations",
    tags=["recommendations"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=RecommendationResponse)
async def get_recommendations(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=100, description="Number of recommendations to return")
):
    """
    Get place recommendations for the current authenticated user.
    """
    if not current_user: # Should be handled by get_current_active_user if token is invalid
        raise HTTPException(status_code=401, detail="Not authenticated")

    recommended_places_models = recommendation_service.get_recommendations_for_user(
        db=db, user_id=current_user.id, limit=limit
    )

    # The recommended_places_models are SQLAlchemy model instances.
    # FastAPI will automatically convert them to a list of PlaceSchema
    # based on the response_model hint for RecommendationResponse which contains List[PlaceSchema].
    return RecommendationResponse(recommendations=recommended_places_models)
