from fastapi import APIRouter, Depends
from app.models.schemas import TripRecommendationByUserResponse
from app.services.recommendation_service import RecommendationService
from app.core.dependencies import get_recommendation_service

router = APIRouter()


@router.get("/recommend-trip/{user_id}", response_model=TripRecommendationByUserResponse)
def recommend_trip_for_user(
    user_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
) -> TripRecommendationByUserResponse:
    return service.get_recommendations_for_user(user_id)

