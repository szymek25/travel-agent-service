from fastapi import APIRouter
from app.api.routes import chat, recommendations, user

api_router = APIRouter()

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(recommendations.router, tags=["recommendations"])
api_router.include_router(user.router, tags=["user"])
