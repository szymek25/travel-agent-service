from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserProfile:
    user_id: str = "default"
    preferred_destinations: List[str] = field(default_factory=list)
    travel_style: Optional[str] = None
    budget: Optional[str] = None
    dietary_restrictions: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)


@dataclass
class TravelRecommendation:
    destination: str
    description: str
    estimated_cost: str
    travel_style: str
    highlights: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    reply: str
    extracted_preferences: dict
    recommendations_preview: List[dict]
