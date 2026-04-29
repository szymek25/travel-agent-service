from app.agents.agent import TravelAgent
from app.models.schemas import ChatRequest, ChatResponse, RecommendationPreview, UserPreferencesSchema
from app.services.user_service import UserService


class ChatService:
    def __init__(self, user_service: UserService) -> None:
        self._agent = TravelAgent()
        self._user_service = user_service

    def handle_message(self, request: ChatRequest) -> ChatResponse:
        user_id = request.user_id or "default"
        existing_preferences = self._user_service.get_preferences(user_id)
        result = self._agent.run(message=request.message, user_preferences=existing_preferences)
        self._user_service.update_from_preferences(user_id, result.extracted_preferences)
        recommendations_preview = [
            RecommendationPreview(**item) for item in result.recommendations_preview
        ]
        return ChatResponse(
            reply=result.reply,
            extracted_preferences=UserPreferencesSchema(
                travel_style=result.extracted_preferences.travel_style,
                budget=result.extracted_preferences.budget,
                preferred_destinations=result.extracted_preferences.preferred_destinations,
                dietary_restrictions=result.extracted_preferences.dietary_restrictions,
                interests=result.extracted_preferences.interests,
            ),
            recommendations_preview=recommendations_preview,
        )
