from fastapi import APIRouter, Depends
from app.models.schemas import TripRecommendationRequest, TripRecommendationResponse
from app.services.recommendation_service import RecommendationService
from app.core.dependencies import get_recommendation_service

router = APIRouter()


@router.post("/recommend-trip", response_model=TripRecommendationResponse)
def recommend_trip(
    request: TripRecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service),
) -> TripRecommendationResponse:
    return service.get_recommendations(request)
