from pydantic import BaseModel
from typing import List
from .places import Place # Use the comprehensive Place schema for now

class RecommendationResponse(BaseModel):
    recommendations: List[Place]

# If a simpler Place representation is desired for recommendations later,
# we can use PlaceRecommendation schema created in places.py:
# from .places import PlaceRecommendation
# class RecommendationResponseSimple(BaseModel):
#     recommendations: List[PlaceRecommendation]
