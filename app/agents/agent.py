from typing import List
import uuid

from strands import Agent as StrandsAgent, tool
from strands.session.file_session_manager import FileSessionManager

from app.agents.preference_extractor import PreferenceExtractorAgent
from app.agents.providers import LLMProvider, create_provider
from app.agents.recommendations_agent import RecommendationsAgent
from app.core.config import settings
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
    "- Once all key preferences are known, call the get_travel_recommendations tool to fetch "
    "personalised destination suggestions from the agency's portfolio, then present them to the user."
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
    def __init__(self, llm_provider: LLMProvider | None = None, session_id: str | None = None) -> None:
        if llm_provider is None:
            llm_provider = create_provider("travel_agent")

        self._recommendations_agent = RecommendationsAgent()
        self._last_recommendations: List[dict] = []

        # Build the recommendations tool as a closure so the Strands agent can call it
        # autonomously when it decides to propose destinations.
        this = self

        @tool
        def get_travel_recommendations(
            travel_style: str = "",
            budget: str = "",
            preferred_destinations: str = "",
            interests: str = "",
        ) -> str:
            """Get personalised destination recommendations from the agency's travel portfolio.
            Call this when you are ready to propose specific destinations to the user.
            Leave parameters empty for any preference that is not yet known.

            Args:
                travel_style: Traveller's style (e.g. beach, adventure, cultural, city break, ski, luxury).
                budget: Budget as a description or amount (e.g. luxury, mid-range, 2000).
                preferred_destinations: Comma-separated preferred destinations or regions.
                interests: Comma-separated interests (e.g. hiking, museums, food tours, diving).
            """
            prefs = UserPreferences(
                travel_style=travel_style or None,
                budget=budget or None,
                preferred_destinations=[d.strip() for d in preferred_destinations.split(",") if d.strip()],
                interests=[i.strip() for i in interests.split(",") if i.strip()],
            )
            recs = this._recommendations_agent.get_recommendations(prefs)
            this._last_recommendations.clear()
            this._last_recommendations.extend(recs)
            if not recs:
                return "No matching recommendations found in the portfolio."
            return "\n".join(f"- {r['destination']}: {r['description']}" for r in recs)

        self._get_travel_recommendations_tool = get_travel_recommendations
        session_manager = FileSessionManager(
            session_id=session_id or str(uuid.uuid4()),
            storage_dir=settings.SESSION_STORAGE_DIR,
        )
        self._agent = StrandsAgent(
            model=llm_provider.get_model(),
            system_prompt=_SYSTEM_PROMPT,
            tools=[get_travel_recommendations],
            state={"user_preferences": {}},
            session_manager=session_manager,
        )
        self._extractor = PreferenceExtractorAgent(llm_provider=llm_provider)

    def run(self, message: str, user_preferences: UserPreferences | None = None) -> AgentResult:
        current_prefs = user_preferences or UserPreferences()

        # Extract preferences from the current message and merge with existing
        extracted = self._extractor.extract(message)
        merged = current_prefs.merge(extracted)

        # Seed agent state with merged preferences
        self._agent.state.set("user_preferences", merged.to_dict())

        # Reset per-turn recommendations; the tool populates this list if called by the agent
        self._last_recommendations.clear()

        # Build context-enriched message so the main agent sees current preferences
        enriched_message = _build_context_message(message, merged)
        result = self._agent(enriched_message)

        return AgentResult(
            reply=str(result),
            extracted_preferences=merged,
            recommendations_preview=list(self._last_recommendations),
        )
