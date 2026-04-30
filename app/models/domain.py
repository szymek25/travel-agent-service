from dataclasses import dataclass, field
from typing import List, Optional

from pydantic import BaseModel, Field


@dataclass
class UserProfile:
    user_id: str = "default"
    preferred_destinations: List[str] = field(default_factory=list)
    travel_style: Optional[str] = None
    budget: Optional[str | int] = None
    dietary_restrictions: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)


@dataclass
class UserPreferences:
    travel_style: Optional[str] = None
    budget: Optional[str | int] = None
    preferred_destinations: List[str] = field(default_factory=list)
    dietary_restrictions: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)

    def merge(self, other: "UserPreferences") -> "UserPreferences":
        """Return a new UserPreferences combining self with other.

        Scalar values from other take precedence when set;
        list fields are unioned.
        """
        return UserPreferences(
            travel_style=other.travel_style or self.travel_style,
            budget=other.budget or self.budget,
            preferred_destinations=list(set(self.preferred_destinations) | set(other.preferred_destinations)),
            dietary_restrictions=list(set(self.dietary_restrictions) | set(other.dietary_restrictions)),
            interests=list(set(self.interests) | set(other.interests)),
        )

    def to_dict(self) -> dict:
        return {
            "travel_style": self.travel_style,
            "budget": self.budget,
            "preferred_destinations": self.preferred_destinations,
            "dietary_restrictions": self.dietary_restrictions,
            "interests": self.interests,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserPreferences":
        return cls(
            travel_style=data.get("travel_style"),
            budget=data.get("budget"),
            preferred_destinations=data.get("preferred_destinations") or [],
            dietary_restrictions=data.get("dietary_restrictions") or [],
            interests=data.get("interests") or [],
        )


@dataclass
class AgentResult:
    reply: str
    extracted_preferences: UserPreferences
    recommendations_preview: List[dict]


class RecommendationItem(BaseModel):
    destination: str = Field(description="Destination name as listed in the portfolio.")
    description: str = Field(description="1-2 sentence personalised description.")


class RecommendationsOutput(BaseModel):
    recommendations: List[RecommendationItem] = Field(
        description="List of 2-3 recommended destinations.",
    )
