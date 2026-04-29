from typing import List

from strands import Agent as StrandsAgent

from app.agents.preference_extractor import PreferenceExtractorAgent
from app.agents.providers import LLMProvider, OllamaProvider
from app.models.domain import AgentResult, UserPreferences

_SYSTEM_PROMPT = (
    "You are a knowledgeable and enthusiastic travel advisor. "
    "Help users plan amazing trips by providing personalized recommendations "
    "based on their preferences, budget, and travel style.\n\n"
    "Each message begins with a [What I know about you so far] section written in plain language. "
    "Fields described as 'not yet known' mean the user has not provided that information yet. "
    "When handling a travel planning request:\n"
    "- If travel style or budget are not yet known and would meaningfully improve your recommendations, "
    "ask the user 1-2 focused follow-up questions to gather the missing information.\n"
    "- You may still provide helpful general advice while asking for clarification.\n"
    "- Once all key preferences are known, give fully tailored, specific recommendations."
)


def _build_context_message(message: str, prefs: UserPreferences) -> str:
    """Prepend a natural-language preferences summary to *message* for the main agent."""

    if prefs.travel_style:
        travel_style_line = f"- Travel style: {prefs.travel_style}."
    else:
        travel_style_line = (
            "- Travel style: not yet known "
            "(e.g. beach, city break, cultural, adventure, luxury)."
        )

    if prefs.budget is not None:
        budget_line = f"- Budget: {prefs.budget}."
    else:
        budget_line = (
            "- Budget: not yet known "
            "(e.g. budget-friendly, mid-range, luxury, or a specific amount like $2000)."
        )

    if prefs.preferred_destinations:
        destinations_line = f"- Preferred destinations: {', '.join(str(d) for d in prefs.preferred_destinations)}."
    else:
        destinations_line = (
            "- Preferred destinations: not yet known "
            "(e.g. Europe, tropical islands, Japan)."
        )

    if prefs.dietary_restrictions:
        dietary_line = f"- Dietary restrictions: {', '.join(str(r) for r in prefs.dietary_restrictions)}."
    else:
        dietary_line = "- Dietary restrictions: none mentioned."

    if prefs.interests:
        interests_line = f"- Interests: {', '.join(str(i) for i in prefs.interests)}."
    else:
        interests_line = (
            "- Interests: not yet known "
            "(e.g. hiking, museums, food tours, diving)."
        )

    lines = [
        "[What I know about you so far]",
        travel_style_line,
        budget_line,
        destinations_line,
        dietary_line,
        interests_line,
        "",
        "[User message]",
        message,
    ]
    return "\n".join(lines)


class TravelAgent:
    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        if llm_provider is None:
            llm_provider = OllamaProvider()
        self._agent = StrandsAgent(
            model=llm_provider.get_model(),
            system_prompt=_SYSTEM_PROMPT,
            state={"user_preferences": {}},
        )
        self._extractor = PreferenceExtractorAgent(llm_provider=llm_provider)

    def run(self, message: str, user_preferences: UserPreferences | None = None) -> AgentResult:
        current_prefs = user_preferences or UserPreferences()

        # Extract preferences from the current message and merge with existing
        extracted = self._extractor.extract(message)
        merged = current_prefs.merge(extracted)

        # Seed agent state with merged preferences
        self._agent.state.set("user_preferences", merged.to_dict())

        # Build context-enriched message so the main agent sees current preferences
        enriched_message = _build_context_message(message, merged)
        result = self._agent(enriched_message)

        recommendations_preview = self._get_recommendations_preview(merged)
        return AgentResult(
            reply=str(result),
            extracted_preferences=merged,
            recommendations_preview=recommendations_preview,
        )

    def _get_recommendations_preview(self, preferences: UserPreferences) -> List[dict]:
        travel_style = preferences.travel_style or ""
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
