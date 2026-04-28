from fastapi import APIRouter, Depends
from app.models.schemas import UserProfileRequest, UserProfileResponse
from app.services.user_service import UserService
from app.core.dependencies import get_user_service

router = APIRouter()


@router.get("/user-profile/{user_id}", response_model=UserProfileResponse)
def get_user_profile(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    return service.get_profile(user_id)


@router.post("/user-profile/{user_id}", response_model=UserProfileResponse)
def update_or_create_user_profile(
    user_id: str,
    request: UserProfileRequest,
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    return service.update_or_create_profile(user_id, request)
