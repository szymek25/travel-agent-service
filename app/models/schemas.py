from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class UserPreferencesSchema(BaseModel):
    travel_style: Optional[str] = None
    budget: Optional[str | int] = None
    preferred_destinations: List[str] = []
    dietary_restrictions: List[str] = []
    interests: List[str] = []


class RecommendationPreview(BaseModel):
    destination: str
    description: str


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    extracted_preferences: UserPreferencesSchema
    recommendations_preview: List[RecommendationPreview]


class TripRecommendationByUserResponse(BaseModel):
    recommendations: List[RecommendationPreview]


class UserProfileRequest(BaseModel):
    preferred_destinations: Optional[List[str]] = None
    travel_style: Optional[str] = None
    budget: Optional[str | int] = None
    dietary_restrictions: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class UserProfileResponse(BaseModel):
    user_id: str
    preferred_destinations: List[str]
    travel_style: Optional[str]
    budget: Optional[str | int]
    dietary_restrictions: List[str]
    interests: List[str]
