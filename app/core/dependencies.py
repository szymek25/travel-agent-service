from app.services.user_service import UserService
from app.services.chat_service import ChatService
from app.services.recommendation_service import RecommendationService

# A single UserService instance is shared across requests by design so that
# in-memory user state persists for the lifetime of the process.
# Replace with a database-backed implementation for multi-instance deployments.
_user_service = UserService()


def get_user_service() -> UserService:
    return _user_service


def get_chat_service() -> ChatService:
    return ChatService(user_service=_user_service)


def get_recommendation_service() -> RecommendationService:
    return RecommendationService()
