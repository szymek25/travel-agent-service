from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agents.agent import TravelAgent, _SYSTEM_PROMPT
from app.agents.providers import BedrockProvider, LLMProvider, OllamaProvider
from app.models.domain import AgentResult, UserPreferences


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_provider(reply: str = "Here are some travel tips!") -> LLMProvider:
    """Return a mock LLMProvider whose StrandsAgent returns `reply`."""
    mock_model = MagicMock()
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.get_model.return_value = mock_model

    mock_agent_result = MagicMock()
    mock_agent_result.__str__ = lambda self: reply

    with patch("app.agents.agent.StrandsAgent") as MockStrandsAgent:
        MockStrandsAgent.return_value = MagicMock(return_value=mock_agent_result)
        agent = TravelAgent(llm_provider=mock_provider)

    # Attach the mocked strands agent so callers can inspect it
    agent._strands_mock_result = mock_agent_result
    return agent


@pytest.fixture
def beach_agent() -> TravelAgent:
    return _make_provider()


# ---------------------------------------------------------------------------
# TravelAgent construction
# ---------------------------------------------------------------------------


class TestTravelAgentConstruction:
    def test_uses_provided_provider(self) -> None:
        mock_model = MagicMock()
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = mock_model

        with patch("app.agents.agent.StrandsAgent") as MockStrandsAgent:
            TravelAgent(llm_provider=provider)
            MockStrandsAgent.assert_called_once_with(model=mock_model, system_prompt=_SYSTEM_PROMPT, state={"user_preferences": {}})

    def test_defaults_to_ollama_provider_when_none_given(self) -> None:
        mock_model = MagicMock()
        with (
            patch("strands.models.ollama.OllamaModel", return_value=mock_model),
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
        ):
            TravelAgent()
            MockStrandsAgent.assert_called_once()
            _, kwargs = MockStrandsAgent.call_args
            assert kwargs["system_prompt"] == _SYSTEM_PROMPT

    def test_system_prompt_is_set(self) -> None:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()

        with patch("app.agents.agent.StrandsAgent") as MockStrandsAgent:
            TravelAgent(llm_provider=provider)
            _, kwargs = MockStrandsAgent.call_args
            assert "travel advisor" in kwargs["system_prompt"].lower()


# ---------------------------------------------------------------------------
# TravelAgent.run
# ---------------------------------------------------------------------------


class TestTravelAgentRun:
    def _make_agent(self, reply: str = "Great trip ahead!") -> TravelAgent:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()

        mock_strands_result = MagicMock()
        mock_strands_result.__str__ = lambda self: reply

        with patch("app.agents.agent.StrandsAgent") as MockStrandsAgent:
            mock_inner = MagicMock(return_value=mock_strands_result)
            MockStrandsAgent.return_value = mock_inner
            agent = TravelAgent(llm_provider=provider)

        return agent

    def test_returns_agent_result_instance(self) -> None:
        agent = self._make_agent()
        result = agent.run("I want to visit a beach.")
        assert isinstance(result, AgentResult)

    def test_reply_comes_from_strands_agent(self) -> None:
        agent = self._make_agent(reply="Enjoy the sun!")
        result = agent.run("beach trip")
        assert result.reply == "Enjoy the sun!"

    def test_strands_agent_called_with_message(self) -> None:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()
        mock_strands_result = MagicMock()
        mock_strands_result.__str__ = lambda self: "ok"

        with patch("app.agents.agent.StrandsAgent") as MockStrandsAgent:
            mock_inner = MagicMock(return_value=mock_strands_result)
            MockStrandsAgent.return_value = mock_inner
            agent = TravelAgent(llm_provider=provider)

        agent.run("I love hiking")
        agent._agent.assert_called_once_with("I love hiking")

    def test_result_contains_extracted_preferences(self) -> None:
        agent = self._make_agent()
        result = agent.run("I want a luxury beach holiday")
        assert result.extracted_preferences.travel_style == "beach"
        assert result.extracted_preferences.budget == "luxury"

    def test_result_contains_recommendations_preview(self) -> None:
        agent = self._make_agent()
        result = agent.run("adventure hiking trip")
        assert isinstance(result.recommendations_preview, list)
        assert len(result.recommendations_preview) > 0

    def test_empty_message_returns_default_recommendations(self) -> None:
        agent = self._make_agent()
        result = agent.run("")
        assert isinstance(result.recommendations_preview, list)
        assert len(result.recommendations_preview) > 0

    def test_empty_message_has_no_extracted_preferences(self) -> None:
        agent = self._make_agent()
        result = agent.run("")
        assert result.extracted_preferences == UserPreferences()


# ---------------------------------------------------------------------------
# TravelAgent._extract_preferences
# ---------------------------------------------------------------------------


class TestExtractPreferences:
    @pytest.fixture(autouse=True)
    def agent(self) -> TravelAgent:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()
        with patch("app.agents.agent.StrandsAgent"):
            self._agent = TravelAgent(llm_provider=provider)

    # Travel style — positive
    def test_beach_keywords(self) -> None:
        for word in ["beach", "sea", "ocean", "coast"]:
            prefs = self._agent._extract_preferences(f"I love the {word}")
            assert prefs.travel_style == "beach", f"failed for keyword: {word}"

    def test_adventure_keywords(self) -> None:
        for word in ["mountain", "hiking", "trek", "adventure"]:
            prefs = self._agent._extract_preferences(f"I enjoy {word}")
            assert prefs.travel_style == "adventure", f"failed for keyword: {word}"

    def test_cultural_keywords(self) -> None:
        for word in ["city", "culture", "museum", "history"]:
            prefs = self._agent._extract_preferences(f"I like {word}")
            assert prefs.travel_style == "cultural", f"failed for keyword: {word}"

    # Travel style — negative / edge cases
    def test_no_style_keyword_omits_travel_style(self) -> None:
        prefs = self._agent._extract_preferences("I want to travel somewhere nice")
        assert prefs.travel_style is None

    def test_style_detection_is_case_insensitive(self) -> None:
        prefs = self._agent._extract_preferences("I love BEACH trips")
        assert prefs.travel_style == "beach"

    def test_first_matching_style_wins(self) -> None:
        # "beach" appears before "mountain" in the elif chain
        prefs = self._agent._extract_preferences("beach and mountain")
        assert prefs.travel_style == "beach"

    # Budget — positive
    def test_budget_keywords(self) -> None:
        for word in ["cheap", "budget", "affordable", "backpacking"]:
            prefs = self._agent._extract_preferences(f"I need {word} options")
            assert prefs.budget == "budget", f"failed for keyword: {word}"

    def test_luxury_keywords(self) -> None:
        for word in ["luxury", "premium", "five star"]:
            prefs = self._agent._extract_preferences(f"I want {word} hotels")
            assert prefs.budget == "luxury", f"failed for keyword: {word}"

    def test_moderate_keywords(self) -> None:
        for word in ["moderate", "mid-range", "comfortable"]:
            prefs = self._agent._extract_preferences(f"I prefer {word} travel")
            assert prefs.budget == "moderate", f"failed for keyword: {word}"

    # Budget — negative / edge cases
    def test_no_budget_keyword_omits_budget(self) -> None:
        prefs = self._agent._extract_preferences("I want to travel")
        assert prefs.budget is None

    def test_budget_detection_is_case_insensitive(self) -> None:
        prefs = self._agent._extract_preferences("I want LUXURY travel")
        assert prefs.budget == "luxury"

    # Destinations — positive
    def test_known_destination_detected(self) -> None:
        prefs = self._agent._extract_preferences("I'd love to visit Paris next year")
        assert "Paris" in prefs.preferred_destinations

    def test_multiple_destinations_detected(self) -> None:
        prefs = self._agent._extract_preferences("Tokyo and Bali are my top choices")
        assert "Tokyo" in prefs.preferred_destinations
        assert "Bali" in prefs.preferred_destinations

    def test_all_known_destinations_detected(self) -> None:
        msg = "paris tokyo new york bali rome london barcelona sydney"
        prefs = self._agent._extract_preferences(msg)
        assert len(prefs.preferred_destinations) == 8

    # Destinations — negative / edge cases
    def test_unknown_destination_not_included(self) -> None:
        prefs = self._agent._extract_preferences("I want to visit Helsinki")
        assert prefs.preferred_destinations == []

    def test_no_destination_omits_key(self) -> None:
        prefs = self._agent._extract_preferences("I like travelling")
        assert prefs.preferred_destinations == []

    def test_destination_title_cased_in_output(self) -> None:
        prefs = self._agent._extract_preferences("I want to go to paris")
        assert "Paris" in prefs.preferred_destinations

    def test_empty_message_returns_empty_dict(self) -> None:
        prefs = self._agent._extract_preferences("")
        assert prefs == UserPreferences()


# ---------------------------------------------------------------------------
# TravelAgent._get_recommendations_preview
# ---------------------------------------------------------------------------


class TestGetRecommendationsPreview:
    @pytest.fixture(autouse=True)
    def agent(self) -> TravelAgent:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()
        with patch("app.agents.agent.StrandsAgent"):
            self._agent = TravelAgent(llm_provider=provider)

    def test_beach_style_returns_beach_destinations(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences(travel_style="beach"))
        destinations = [r["destination"] for r in recs]
        assert any("Bali" in d or "Maldives" in d for d in destinations)

    def test_adventure_style_returns_adventure_destinations(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences(travel_style="adventure"))
        destinations = [r["destination"] for r in recs]
        assert any("Patagonia" in d or "Nepal" in d for d in destinations)

    def test_cultural_style_returns_cultural_destinations(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences(travel_style="cultural"))
        destinations = [r["destination"] for r in recs]
        assert any("Kyoto" in d or "Rome" in d for d in destinations)

    def test_unknown_style_returns_default_recommendations(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences(travel_style="unknown_style"))
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_missing_travel_style_returns_default_recommendations(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences())
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_default_recommendations_include_paris_and_tokyo(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences())
        destinations = [r["destination"] for r in recs]
        assert any("Paris" in d for d in destinations)
        assert any("Tokyo" in d for d in destinations)

    def test_each_recommendation_has_destination_and_description(self) -> None:
        for style in ["beach", "adventure", "cultural", ""]:
            recs = self._agent._get_recommendations_preview(UserPreferences(travel_style=style or None))
            for rec in recs:
                assert "destination" in rec
                assert "description" in rec
                assert isinstance(rec["destination"], str)
                assert isinstance(rec["description"], str)

    def test_empty_preferences_returns_list(self) -> None:
        recs = self._agent._get_recommendations_preview(UserPreferences())
        assert isinstance(recs, list)


# ---------------------------------------------------------------------------
# OllamaProvider
# ---------------------------------------------------------------------------


class TestOllamaProvider:
    def test_uses_explicit_host_and_model(self) -> None:
        provider = OllamaProvider(host="http://custom:11434", model_id="mistral")
        assert provider.host == "http://custom:11434"
        assert provider.model_id == "mistral"

    def test_falls_back_to_settings(self) -> None:
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.OLLAMA_HOST = "http://settings-host:11434"
            mock_settings.OLLAMA_MODEL_ID = "settings-model"
            provider = OllamaProvider()
        assert provider.host == "http://settings-host:11434"
        assert provider.model_id == "settings-model"

    def test_explicit_values_override_settings(self) -> None:
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.OLLAMA_HOST = "http://ignored:11434"
            mock_settings.OLLAMA_MODEL_ID = "ignored"
            provider = OllamaProvider(host="http://explicit:11434", model_id="llama3.2")
        assert provider.host == "http://explicit:11434"
        assert provider.model_id == "llama3.2"

    def test_get_model_returns_ollama_model_instance(self) -> None:
        mock_model = MagicMock()
        with patch("strands.models.ollama.OllamaModel", return_value=mock_model) as MockOllama:
            provider = OllamaProvider(host="http://localhost:11434", model_id="llama3.1")
            result = provider.get_model()
        MockOllama.assert_called_once_with(host="http://localhost:11434", model_id="llama3.1")
        assert result is mock_model

    def test_get_model_called_with_correct_args(self) -> None:
        with patch("strands.models.ollama.OllamaModel") as MockOllama:
            provider = OllamaProvider(host="http://myhost:11434", model_id="phi3")
            provider.get_model()
            MockOllama.assert_called_once_with(host="http://myhost:11434", model_id="phi3")


# ---------------------------------------------------------------------------
# BedrockProvider
# ---------------------------------------------------------------------------


class TestBedrockProvider:
    def test_uses_explicit_model_id_and_region(self) -> None:
        provider = BedrockProvider(model_id="my.model", region_name="eu-west-1")
        assert provider.model_id == "my.model"
        assert provider.region_name == "eu-west-1"

    def test_falls_back_to_settings(self) -> None:
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.BEDROCK_MODEL_ID = "settings.model"
            mock_settings.AWS_REGION = "us-west-2"
            provider = BedrockProvider()
        assert provider.model_id == "settings.model"
        assert provider.region_name == "us-west-2"

    def test_explicit_values_override_settings(self) -> None:
        with patch("app.core.config.settings") as mock_settings:
            mock_settings.BEDROCK_MODEL_ID = "ignored"
            mock_settings.AWS_REGION = "ignored"
            provider = BedrockProvider(model_id="explicit.model", region_name="ap-southeast-1")
        assert provider.model_id == "explicit.model"
        assert provider.region_name == "ap-southeast-1"

    def test_get_model_returns_bedrock_model_instance(self) -> None:
        mock_model = MagicMock()
        with patch("strands.models.BedrockModel", return_value=mock_model) as MockBedrock:
            provider = BedrockProvider(model_id="my.model", region_name="us-east-1")
            result = provider.get_model()
        MockBedrock.assert_called_once_with(model_id="my.model", region_name="us-east-1")
        assert result is mock_model

    def test_get_model_called_with_correct_args(self) -> None:
        with patch("strands.models.BedrockModel") as MockBedrock:
            provider = BedrockProvider(model_id="anthropic.claude", region_name="eu-central-1")
            provider.get_model()
            MockBedrock.assert_called_once_with(model_id="anthropic.claude", region_name="eu-central-1")
