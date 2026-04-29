from unittest.mock import MagicMock, patch

import pytest
from strands.types.exceptions import StructuredOutputException

from app.agents.preference_extractor import PreferenceExtractorAgent, _PreferencesOutput
from app.agents.providers import LLMProvider
from app.models.domain import UserPreferences


def _make_extractor() -> PreferenceExtractorAgent:
    provider = MagicMock(spec=LLMProvider)
    provider.get_model.return_value = MagicMock()
    return PreferenceExtractorAgent(llm_provider=provider)


def _run_extract(
    extractor: PreferenceExtractorAgent,
    message: str,
    structured_output: _PreferencesOutput,
) -> UserPreferences:
    mock_agent_result = MagicMock()
    mock_agent_result.structured_output = structured_output
    with patch("app.agents.preference_extractor.StrandsAgent") as MockStrandsAgent:
        MockStrandsAgent.return_value = MagicMock(return_value=mock_agent_result)
        return extractor.extract(message)


# ---------------------------------------------------------------------------
# _PreferencesOutput validators  (unit tests — no LLM needed)
# ---------------------------------------------------------------------------


class TestPreferencesOutputValidators:
    def test_null_scalars_stay_none(self) -> None:
        out = _PreferencesOutput(travel_style=None, budget=None)
        assert out.travel_style is None
        assert out.budget is None

    # travel_style
    def test_arbitrary_travel_style_accepted(self) -> None:
        assert _PreferencesOutput(travel_style="ski").travel_style == "ski"

    def test_non_english_travel_style_accepted(self) -> None:
        assert _PreferencesOutput(travel_style="przygodowy").travel_style == "przygodowy"

    def test_travel_style_whitespace_stripped(self) -> None:
        assert _PreferencesOutput(travel_style="  beach  ").travel_style == "beach"

    def test_empty_string_travel_style_becomes_none(self) -> None:
        assert _PreferencesOutput(travel_style="").travel_style is None

    def test_various_travel_styles_accepted(self) -> None:
        for style in ("beach", "adventure", "cultural", "ski", "road-trip", "plażowy"):
            assert _PreferencesOutput(travel_style=style).travel_style == style

    # budget — numeric
    def test_integer_budget_accepted(self) -> None:
        out = _PreferencesOutput(budget=2000)
        assert out.budget == 2000
        assert isinstance(out.budget, int)

    def test_float_budget_normalised_to_int(self) -> None:
        out = _PreferencesOutput(budget=1500.0)
        assert out.budget == 1500
        assert isinstance(out.budget, int)

    def test_negative_budget_coerced_to_none(self) -> None:
        assert _PreferencesOutput(budget=-500).budget is None

    def test_zero_budget_coerced_to_none(self) -> None:
        assert _PreferencesOutput(budget=0).budget is None

    def test_boolean_budget_coerced_to_none(self) -> None:
        assert _PreferencesOutput(budget=True).budget is None

    # budget — string
    def test_arbitrary_budget_string_accepted(self) -> None:
        assert _PreferencesOutput(budget="ekonomiczny").budget == "ekonomiczny"

    def test_budget_string_whitespace_stripped(self) -> None:
        assert _PreferencesOutput(budget="  luxury  ").budget == "luxury"

    def test_empty_string_budget_becomes_none(self) -> None:
        assert _PreferencesOutput(budget="").budget is None

    def test_various_budget_strings_accepted(self) -> None:
        for budget in ("budget", "moderate", "luxury", "oszczędny", "tani", "cheap"):
            assert _PreferencesOutput(budget=budget).budget == budget

    # lists
    def test_defaults_to_empty_lists(self) -> None:
        out = _PreferencesOutput()
        assert out.preferred_destinations == []
        assert out.dietary_restrictions == []
        assert out.interests == []

    def test_null_list_fields_coerced_to_empty(self) -> None:
        out = _PreferencesOutput(
            preferred_destinations=None,  # type: ignore[arg-type]
            dietary_restrictions=None,  # type: ignore[arg-type]
            interests=None,  # type: ignore[arg-type]
        )
        assert out.preferred_destinations == []
        assert out.dietary_restrictions == []
        assert out.interests == []

    def test_non_list_list_fields_coerced_to_empty(self) -> None:
        out = _PreferencesOutput(
            preferred_destinations="Paris",  # type: ignore[arg-type]
            dietary_restrictions="vegan",  # type: ignore[arg-type]
            interests="hiking",  # type: ignore[arg-type]
        )
        assert out.preferred_destinations == []
        assert out.dietary_restrictions == []
        assert out.interests == []


# ---------------------------------------------------------------------------
# PreferenceExtractorAgent.extract  (integration — StrandsAgent mocked)
# ---------------------------------------------------------------------------


class TestPreferenceExtractorExtract:
    def test_returns_user_preferences_instance(self) -> None:
        result = _run_extract(_make_extractor(), "beach trip", _PreferencesOutput(travel_style="beach"))
        assert isinstance(result, UserPreferences)

    def test_maps_travel_style(self) -> None:
        result = _run_extract(_make_extractor(), "I love hiking", _PreferencesOutput(travel_style="adventure"))
        assert result.travel_style == "adventure"

    def test_maps_budget_string(self) -> None:
        result = _run_extract(_make_extractor(), "luxury holiday", _PreferencesOutput(budget="luxury"))
        assert result.budget == "luxury"

    def test_maps_budget_integer(self) -> None:
        result = _run_extract(_make_extractor(), "I have 3000 to spend", _PreferencesOutput(budget=3000))
        assert result.budget == 3000

    def test_maps_destinations(self) -> None:
        result = _run_extract(
            _make_extractor(),
            "I want to visit Tokyo and Bali",
            _PreferencesOutput(preferred_destinations=["Tokyo", "Bali"]),
        )
        assert "Tokyo" in result.preferred_destinations
        assert "Bali" in result.preferred_destinations

    def test_maps_dietary_restrictions(self) -> None:
        result = _run_extract(_make_extractor(), "I am vegan", _PreferencesOutput(dietary_restrictions=["vegan"]))
        assert "vegan" in result.dietary_restrictions

    def test_maps_interests(self) -> None:
        result = _run_extract(_make_extractor(), "I love museums", _PreferencesOutput(interests=["museums"]))
        assert "museums" in result.interests

    def test_passes_structured_output_model_to_agent(self) -> None:
        extractor = _make_extractor()
        mock_agent_result = MagicMock()
        mock_agent_result.structured_output = _PreferencesOutput()
        with patch("app.agents.preference_extractor.StrandsAgent") as MockStrandsAgent:
            mock_agent = MagicMock(return_value=mock_agent_result)
            MockStrandsAgent.return_value = mock_agent
            extractor.extract("beach trip")
            _, kwargs = mock_agent.call_args
            assert kwargs.get("structured_output_model") is _PreferencesOutput

    def test_structured_output_exception_returns_empty_preferences(self) -> None:
        extractor = _make_extractor()
        with patch("app.agents.preference_extractor.StrandsAgent") as MockStrandsAgent:
            mock_agent = MagicMock(side_effect=StructuredOutputException("extraction failed"))
            MockStrandsAgent.return_value = mock_agent
            result = extractor.extract("beach trip")
        assert result == UserPreferences()

    def test_empty_message_returns_empty_preferences_without_calling_llm(self) -> None:
        extractor = _make_extractor()
        with patch("app.agents.preference_extractor.StrandsAgent") as MockStrandsAgent:
            result = extractor.extract("")
            MockStrandsAgent.assert_not_called()
        assert result == UserPreferences()

    def test_whitespace_only_message_skips_llm(self) -> None:
        extractor = _make_extractor()
        with patch("app.agents.preference_extractor.StrandsAgent") as MockStrandsAgent:
            result = extractor.extract("   ")
            MockStrandsAgent.assert_not_called()
        assert result == UserPreferences()

    def test_new_strands_agent_created_per_extract_call(self) -> None:
        extractor = _make_extractor()
        mock_agent_result = MagicMock()
        mock_agent_result.structured_output = _PreferencesOutput()
        with patch("app.agents.preference_extractor.StrandsAgent") as MockStrandsAgent:
            MockStrandsAgent.return_value = MagicMock(return_value=mock_agent_result)
            extractor.extract("first message")
            extractor.extract("second message")
            assert MockStrandsAgent.call_count == 2
