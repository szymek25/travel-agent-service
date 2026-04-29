import uuid

from app.agents.agent import TravelAgent
from app.models.schemas import ChatRequest, ChatResponse, RecommendationPreview, UserPreferencesSchema
from app.services.user_service import UserService


class ChatService:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    def handle_message(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id or "default"
        existing_preferences = self._user_service.get_preferences(user_id)
        agent = TravelAgent(session_id=session_id)
        result = agent.run(message=request.message, user_preferences=existing_preferences)
        self._user_service.update_from_preferences(user_id, result.extracted_preferences)
        recommendations_preview = [
            RecommendationPreview(**item) for item in result.recommendations_preview
        ]
        return ChatResponse(
            reply=result.reply,
            session_id=session_id,
            extracted_preferences=UserPreferencesSchema(
                travel_style=result.extracted_preferences.travel_style,
                budget=result.extracted_preferences.budget,
                preferred_destinations=result.extracted_preferences.preferred_destinations,
                dietary_restrictions=result.extracted_preferences.dietary_restrictions,
                interests=result.extracted_preferences.interests,
            ),
            recommendations_preview=recommendations_preview,
        )
