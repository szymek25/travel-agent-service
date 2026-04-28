from fastapi import APIRouter, Depends
from app.models.schemas import UserProfileRequest, UserProfileResponse
from app.services.user_service import UserService
from app.core.dependencies import get_user_service

router = APIRouter()


@router.get("/user-profile", response_model=UserProfileResponse)
def get_user_profile(service: UserService = Depends(get_user_service)) -> UserProfileResponse:
    return service.get_profile()


@router.post("/user-profile", response_model=UserProfileResponse)
def update_user_profile(
    request: UserProfileRequest,
    service: UserService = Depends(get_user_service),
) -> UserProfileResponse:
    return service.update_profile(request)
