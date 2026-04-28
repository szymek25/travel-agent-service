from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class RecommendationPreview(BaseModel):
    destination: str
    description: str


class ChatResponse(BaseModel):
    reply: str
    extracted_preferences: dict
    recommendations_preview: List[RecommendationPreview]


class TripRecommendationRequest(BaseModel):
    destination: Optional[str] = None
    travel_style: Optional[str] = None
    budget: Optional[str] = None


class TripRecommendation(BaseModel):
    destination: str
    description: str
    estimated_cost: str
    travel_style: str
    highlights: List[str]


class TripRecommendationResponse(BaseModel):
    recommendations: List[TripRecommendation]


class UserProfileRequest(BaseModel):
    preferred_destinations: Optional[List[str]] = None
    travel_style: Optional[str] = None
    budget: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class UserProfileResponse(BaseModel):
    user_id: str
    preferred_destinations: List[str]
    travel_style: Optional[str]
    budget: Optional[str]
    dietary_restrictions: List[str]
    interests: List[str]
