from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from strands import Agent as StrandsAgent
from strands.types.exceptions import StructuredOutputException

from app.agents.providers import LLMProvider, create_provider
from app.models.domain import UserPreferences

_EXTRACTION_SYSTEM_PROMPT = (
    "You are a travel preference extraction assistant. "
    "Analyze the user message and extract any travel preferences that are explicitly or clearly implied. "
    "Extract only what the user explicitly mentions or strongly implies. "
    "For budget: use a positive integer when the user states a specific amount; "
    "otherwise use a short descriptive string in whatever language the user is writing in. "
    "Use null for any field that is not mentioned."
)


class _PreferencesOutput(BaseModel):
    """Pydantic schema used as structured output target for preference extraction."""

    travel_style: Optional[str] = Field(
        default=None,
        description=(
            "Short description of the travel style "
            "(e.g. beach, adventure, cultural, ski, road-trip). "
            "Use null if not mentioned."
        ),
    )
    budget: Optional[Union[int, str]] = Field(
        default=None,
        description=(
            "A positive integer amount when the user states a specific sum, "
            "or a short descriptive string (e.g. 'budget', 'luxury', 'ekonomiczny') "
            "when they use a general term. Use null if not mentioned."
        ),
    )
    preferred_destinations: List[str] = Field(
        default_factory=list,
        description="List of destination names mentioned by the user.",
    )
    dietary_restrictions: List[str] = Field(
        default_factory=list,
        description="List of dietary restrictions mentioned by the user.",
    )
    interests: List[str] = Field(
        default_factory=list,
        description="List of travel interests mentioned by the user.",
    )

    @field_validator("travel_style", mode="before")
    @classmethod
    def _normalise_travel_style(cls, v: object) -> Optional[str]:
        if not isinstance(v, str) or not v.strip():
            return None
        return v.strip()

    @field_validator("budget", mode="before")
    @classmethod
    def _normalise_budget(cls, v: object) -> Optional[Union[int, str]]:
        if isinstance(v, bool):
            return None
        if isinstance(v, (int, float)) and v > 0:
            return int(v)
        if isinstance(v, str) and v.strip():
            return v.strip()
        return None

    @field_validator("preferred_destinations", "dietary_restrictions", "interests", mode="before")
    @classmethod
    def _coerce_list(cls, v: object) -> list:
        if isinstance(v, list):
            return v
        return []


class PreferenceExtractorAgent:
    """LLM-backed agent that extracts structured UserPreferences from a free-text message."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        if llm_provider is None:
            llm_provider = create_provider("extractor_agent")
        self._model = llm_provider.get_model()

    def extract(self, message: str) -> UserPreferences:
        """Run the extraction agent on *message* and return a UserPreferences instance."""
        if not message or not message.strip():
            return UserPreferences()

        agent = StrandsAgent(model=self._model, system_prompt=_EXTRACTION_SYSTEM_PROMPT)
        try:
            result = agent(message, structured_output_model=_PreferencesOutput)
            output: _PreferencesOutput = result.structured_output
        except StructuredOutputException:
            return UserPreferences()

        return UserPreferences(
            travel_style=output.travel_style,
            budget=output.budget,
            preferred_destinations=output.preferred_destinations,
            dietary_restrictions=output.dietary_restrictions,
            interests=output.interests,
        )
