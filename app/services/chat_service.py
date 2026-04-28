from app.agents.agent import TravelAgent
from app.models.schemas import ChatRequest, ChatResponse, RecommendationPreview
from app.services.user_service import UserService


class ChatService:
    def __init__(self, user_service: UserService) -> None:
        self._agent = TravelAgent()
        self._user_service = user_service

    def handle_message(self, request: ChatRequest) -> ChatResponse:
        result = self._agent.run(message=request.message)
        self._user_service.update_from_preferences(result.extracted_preferences)
        recommendations_preview = [
            RecommendationPreview(**item) for item in result.recommendations_preview
        ]
        return ChatResponse(
            reply=result.reply,
            extracted_preferences=result.extracted_preferences,
            recommendations_preview=recommendations_preview,
        )
