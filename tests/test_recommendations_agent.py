"""Tests for RecommendationsAgent and helpers."""

from unittest.mock import MagicMock, patch

import pytest
from strands.types.exceptions import StructuredOutputException

from app.agents.recommendations_agent import (
    RecommendationsAgent,
    _build_preferences_context,
)
from app.agents.providers import LLMProvider
from app.models.domain import RecommendationItem, RecommendationsOutput, UserPreferences


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_agent() -> RecommendationsAgent:
    provider = MagicMock(spec=LLMProvider)
    provider.get_model.return_value = MagicMock()
    return RecommendationsAgent(llm_provider=provider)


def _run_get_recommendations(
    agent: RecommendationsAgent,
    preferences: UserPreferences,
    structured_output: RecommendationsOutput,
) -> RecommendationsOutput:
    """Call get_recommendations with a mocked StrandsAgent that returns *structured_output*."""
    with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
        MockAgent.return_value = MagicMock(return_value=structured_output)
        return agent.get_recommendations(preferences)


# ---------------------------------------------------------------------------
# _build_preferences_context
# ---------------------------------------------------------------------------


class TestBuildPreferencesContext:
    def test_starts_with_traveller_profile_header(self) -> None:
        result = _build_preferences_context(UserPreferences())
        assert result.startswith("[Traveller profile]")

    def test_none_travel_style_shown_as_not_specified(self) -> None:
        result = _build_preferences_context(UserPreferences())
        assert "Travel style: not specified" in result

    def test_travel_style_rendered_when_set(self) -> None:
        result = _build_preferences_context(UserPreferences(travel_style="adventure"))
        assert "Travel style: adventure" in result

    def test_none_budget_shown_as_not_specified(self) -> None:
        result = _build_preferences_context(UserPreferences())
        assert "Budget: not specified" in result

    def test_string_budget_rendered(self) -> None:
        result = _build_preferences_context(UserPreferences(budget="luxury"))
        assert "Budget: luxury" in result

    def test_integer_budget_rendered(self) -> None:
        result = _build_preferences_context(UserPreferences(budget=2000))
        assert "Budget: 2000" in result

    def test_empty_destinations_shown_as_no_preference(self) -> None:
        result = _build_preferences_context(UserPreferences())
        assert "Preferred destinations: no preference" in result

    def test_single_destination_rendered(self) -> None:
        result = _build_preferences_context(UserPreferences(preferred_destinations=["Japan"]))
        assert "Japan" in result

    def test_multiple_destinations_rendered(self) -> None:
        prefs = UserPreferences(preferred_destinations=["Japan", "Italy", "Peru"])
        result = _build_preferences_context(prefs)
        assert "Japan" in result
        assert "Italy" in result
        assert "Peru" in result

    def test_dietary_line_omitted_when_empty(self) -> None:
        result = _build_preferences_context(UserPreferences())
        assert "Dietary restrictions" not in result

    def test_dietary_line_included_when_set(self) -> None:
        prefs = UserPreferences(dietary_restrictions=["halal", "nut-free"])
        result = _build_preferences_context(prefs)
        assert "Dietary restrictions" in result
        assert "halal" in result
        assert "nut-free" in result

    def test_empty_interests_shown_as_not_specified(self) -> None:
        result = _build_preferences_context(UserPreferences())
        assert "Interests: not specified" in result

    def test_interests_rendered_when_set(self) -> None:
        prefs = UserPreferences(interests=["museums", "food tours", "hiking"])
        result = _build_preferences_context(prefs)
        assert "museums" in result
        assert "food tours" in result
        assert "hiking" in result

    def test_full_preferences_all_present(self) -> None:
        prefs = UserPreferences(
            travel_style="beach",
            budget="luxury",
            preferred_destinations=["Bali", "Maldives"],
            dietary_restrictions=["vegan"],
            interests=["diving", "snorkelling"],
        )
        result = _build_preferences_context(prefs)
        assert "Travel style: beach" in result
        assert "Budget: luxury" in result
        assert "Bali" in result
        assert "Maldives" in result
        assert "Dietary restrictions" in result
        assert "vegan" in result
        assert "diving" in result
        assert "snorkelling" in result


# ---------------------------------------------------------------------------
# RecommendationItem and RecommendationsOutput schemas
# ---------------------------------------------------------------------------


class TestRecommendationSchemas:
    def test_recommendation_item_stores_destination(self) -> None:
        item = RecommendationItem(destination="Bali, Indonesia", description="Stunning beaches.")
        assert item.destination == "Bali, Indonesia"

    def test_recommendation_item_stores_description(self) -> None:
        item = RecommendationItem(destination="Nepal", description="Himalayan trekking.")
        assert item.description == "Himalayan trekking."

    def test_recommendations_output_stores_list(self) -> None:
        items = [
            RecommendationItem(destination="Bali, Indonesia", description="Beaches."),
            RecommendationItem(destination="Nepal", description="Trekking."),
        ]
        output = RecommendationsOutput(recommendations=items)
        assert len(output.recommendations) == 2

    def test_recommendations_output_accepts_empty_list(self) -> None:
        output = RecommendationsOutput(recommendations=[])
        assert output.recommendations == []

    def test_recommendations_output_preserves_order(self) -> None:
        items = [
            RecommendationItem(destination="First", description="d1"),
            RecommendationItem(destination="Second", description="d2"),
            RecommendationItem(destination="Third", description="d3"),
        ]
        output = RecommendationsOutput(recommendations=items)
        assert output.recommendations[0].destination == "First"
        assert output.recommendations[2].destination == "Third"


# ---------------------------------------------------------------------------
# RecommendationsAgent.get_recommendations
# ---------------------------------------------------------------------------


class TestRecommendationsAgentGetRecommendations:
    # --- return type and shape ---

    def test_returns_recommendations_output(self) -> None:
        agent = _make_agent()
        result = _run_get_recommendations(
            agent, UserPreferences(), RecommendationsOutput(recommendations=[])
        )
        assert isinstance(result, RecommendationsOutput)

    def test_returns_empty_recommendations_when_no_results(self) -> None:
        agent = _make_agent()
        result = _run_get_recommendations(
            agent, UserPreferences(), RecommendationsOutput(recommendations=[])
        )
        assert result.recommendations == []

    def test_each_item_has_destination_attribute(self) -> None:
        agent = _make_agent()
        output = RecommendationsOutput(
            recommendations=[RecommendationItem(destination="Nepal", description="Trekking.")]
        )
        result = _run_get_recommendations(agent, UserPreferences(), output)
        assert result.recommendations[0].destination == "Nepal"

    def test_each_item_has_description_attribute(self) -> None:
        agent = _make_agent()
        output = RecommendationsOutput(
            recommendations=[RecommendationItem(destination="Nepal", description="Trekking.")]
        )
        result = _run_get_recommendations(agent, UserPreferences(), output)
        assert result.recommendations[0].description == "Trekking."

    def test_values_match_model_fields(self) -> None:
        agent = _make_agent()
        output = RecommendationsOutput(
            recommendations=[
                RecommendationItem(destination="Patagonia", description="Dramatic landscapes.")
            ]
        )
        result = _run_get_recommendations(agent, UserPreferences(), output)
        assert result.recommendations[0].destination == "Patagonia"
        assert result.recommendations[0].description == "Dramatic landscapes."

    def test_multiple_recommendations_all_returned(self) -> None:
        agent = _make_agent()
        output = RecommendationsOutput(
            recommendations=[
                RecommendationItem(destination="Bali", description="Beaches."),
                RecommendationItem(destination="Nepal", description="Trekking."),
                RecommendationItem(destination="Kyoto", description="Culture."),
            ]
        )
        result = _run_get_recommendations(agent, UserPreferences(), output)
        assert len(result.recommendations) == 3

    # --- error handling ---

    def test_structured_output_exception_returns_empty_output(self) -> None:
        agent = _make_agent()
        with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
            mock_inner = MagicMock(side_effect=StructuredOutputException("validation failed"))
            MockAgent.return_value = mock_inner
            result = agent.get_recommendations(UserPreferences())
        assert isinstance(result, RecommendationsOutput)
        assert result.recommendations == []

    # --- agent interaction ---

    def test_passes_structured_output_model_to_agent(self) -> None:
        agent = _make_agent()
        with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
            mock_inner = MagicMock(return_value=RecommendationsOutput(recommendations=[]))
            MockAgent.return_value = mock_inner
            agent.get_recommendations(UserPreferences())
        _, call_kwargs = mock_inner.call_args
        assert call_kwargs.get("structured_output_model") is RecommendationsOutput

    def test_passes_context_string_containing_header_to_agent(self) -> None:
        agent = _make_agent()
        with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
            mock_inner = MagicMock(return_value=RecommendationsOutput(recommendations=[]))
            MockAgent.return_value = mock_inner
            agent.get_recommendations(UserPreferences())
        context_arg = mock_inner.call_args[0][0]
        assert "[Traveller profile]" in context_arg

    def test_preferences_travel_style_passed_in_context(self) -> None:
        prefs = UserPreferences(travel_style="beach")
        agent = _make_agent()
        with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
            mock_inner = MagicMock(return_value=RecommendationsOutput(recommendations=[]))
            MockAgent.return_value = mock_inner
            agent.get_recommendations(prefs)
        context_arg = mock_inner.call_args[0][0]
        assert "beach" in context_arg

    def test_preferences_interests_passed_in_context(self) -> None:
        prefs = UserPreferences(interests=["scuba diving", "photography"])
        agent = _make_agent()
        with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
            mock_inner = MagicMock(return_value=RecommendationsOutput(recommendations=[]))
            MockAgent.return_value = mock_inner
            agent.get_recommendations(prefs)
        context_arg = mock_inner.call_args[0][0]
        assert "scuba diving" in context_arg

    def test_new_strands_agent_created_per_call(self) -> None:
        """Each call must create a fresh agent to avoid accumulated conversation history."""
        agent = _make_agent()
        with patch("app.agents.recommendations_agent.StrandsAgent") as MockAgent:
            mock_inner = MagicMock(return_value=RecommendationsOutput(recommendations=[]))
            MockAgent.return_value = mock_inner
            agent.get_recommendations(UserPreferences())
            agent.get_recommendations(UserPreferences())
        assert MockAgent.call_count == 2

