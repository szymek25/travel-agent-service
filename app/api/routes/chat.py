from fastapi import APIRouter, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.core.dependencies import get_chat_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)) -> ChatResponse:
    return service.handle_message(request)
