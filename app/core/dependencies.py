from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.recommendation_service import RecommendationService


def get_user_service() -> UserService:
    return UserService()


def get_chat_service() -> ChatService:
    return ChatService(user_service=UserService())


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()
