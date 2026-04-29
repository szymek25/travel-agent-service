from typing import List

from strands import Agent as StrandsAgent

from app.agents.providers import LLMProvider, OllamaProvider
from app.models.domain import AgentResult

_SYSTEM_PROMPT = (
    "You are a knowledgeable and enthusiastic travel advisor. "
    "Help users plan amazing trips by providing personalized recommendations "
    "based on their preferences, budget, and travel style."
)


class TravelAgent:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        if llm_provider is None:
            llm_provider = OllamaProvider()
        self._agent = StrandsAgent(
            model=llm_provider.get_model(),
            system_prompt=_SYSTEM_PROMPT,
        )

    def run(self, message: str) -> AgentResult:
        result = self._agent(message)
        extracted_preferences = self._extract_preferences(message)
        recommendations_preview = self._get_recommendations_preview(extracted_preferences)
        return AgentResult(
            reply=str(result),
            extracted_preferences=extracted_preferences,
            recommendations_preview=recommendations_preview,
        )

    def _extract_preferences(self, message: str) -> dict:
        preferences: dict = {}
        message_lower = message.lower()

        if any(word in message_lower for word in ["beach", "sea", "ocean", "coast"]):
            preferences["travel_style"] = "beach"
        elif any(word in message_lower for word in ["mountain", "hiking", "trek", "adventure"]):
            preferences["travel_style"] = "adventure"
        elif any(word in message_lower for word in ["city", "culture", "museum", "history"]):
            preferences["travel_style"] = "cultural"

        if any(word in message_lower for word in ["cheap", "budget", "affordable", "backpacking"]):
            preferences["budget"] = "budget"
        elif any(word in message_lower for word in ["luxury", "premium", "first class", "five star"]):
            preferences["budget"] = "luxury"
        elif any(word in message_lower for word in ["moderate", "mid-range", "comfortable"]):
            preferences["budget"] = "moderate"

        destinations = []
        known_destinations = ["paris", "tokyo", "new york", "bali", "rome", "london", "barcelona", "sydney"]
        for dest in known_destinations:
            if dest in message_lower:
                destinations.append(dest.title())
        if destinations:
            preferences["preferred_destinations"] = destinations

        return preferences

    def _get_recommendations_preview(self, preferences: dict) -> List[dict]:
        travel_style = preferences.get("travel_style", "")
        style_map = {
            "beach": [
                {"destination": "Bali, Indonesia", "description": "Stunning beaches and vibrant culture."},
                {"destination": "Maldives", "description": "Crystal clear waters and luxury overwater bungalows."},
            ],
            "adventure": [
                {"destination": "Patagonia, Argentina", "description": "Dramatic landscapes and world-class hiking."},
                {"destination": "Nepal", "description": "Gateway to the Himalayas and legendary trekking routes."},
            ],
            "cultural": [
                {"destination": "Kyoto, Japan", "description": "Ancient temples and traditional Japanese culture."},
                {"destination": "Rome, Italy", "description": "Millennia of history, art, and cuisine."},
            ],
        }
        return style_map.get(
            travel_style,
            [
                {"destination": "Paris, France", "description": "The city of light, love, and world-class cuisine."},
                {"destination": "Tokyo, Japan", "description": "A perfect blend of tradition and futuristic innovation."},
            ],
        )
