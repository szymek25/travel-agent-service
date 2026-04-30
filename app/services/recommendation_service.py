from typing import List, Optional
from app.agents.recommendations_agent import RecommendationsAgent
from app.models.domain import UserPreferences
from app.models.schemas import (
    RecommendationPreview,
    TripRecommendationByUserResponse,
)
from app.services.user_service import UserService


class RecommendationService:
    def __init__(
        self,
        user_service: Optional[UserService] = None,
        recommendations_agent: Optional[RecommendationsAgent] = None,
    ) -> None:
        self._user_service = user_service
        self._recommendations_agent = recommendations_agent

    def get_recommendations_for_user(self, user_id: str) -> TripRecommendationByUserResponse:
        profile = self._user_service.get_profile(user_id)
        preferences = UserPreferences(
            travel_style=profile.travel_style,
            budget=profile.budget,
            preferred_destinations=profile.preferred_destinations,
            dietary_restrictions=profile.dietary_restrictions,
            interests=profile.interests,
        )
        results = self._recommendations_agent.get_recommendations(preferences).structured_output
        return TripRecommendationByUserResponse(
            recommendations=[
                RecommendationPreview(destination=r.destination, description=r.description)
                for r in results.recommendations
            ]
        )
