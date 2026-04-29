from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agents.agent import TravelAgent, _SYSTEM_PROMPT, _build_context_message
from app.agents.providers import BedrockProvider, LLMProvider, OllamaProvider
from app.agents.recommendations_agent import RecommendationsAgent
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

    with (
        patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
        patch("app.agents.agent.RecommendationsAgent"),
    ):
        MockStrandsAgent.return_value = MagicMock(return_value=mock_agent_result)
        agent = TravelAgent(llm_provider=mock_provider)

    # Stub out the extractor so tests don't hit a real LLM
    agent._extractor = MagicMock()
    agent._extractor.extract.return_value = UserPreferences()

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

        with (
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            TravelAgent(llm_provider=provider)
            _, kwargs = MockStrandsAgent.call_args
            assert kwargs["model"] is mock_model
            assert kwargs["system_prompt"] == _SYSTEM_PROMPT
            assert kwargs["state"] == {"user_preferences": {}}
            # Tool list should contain exactly the recommendations tool
            assert len(kwargs["tools"]) == 1
            assert kwargs["tools"][0].tool_name == "get_travel_recommendations"

    def test_defaults_to_ollama_provider_when_none_given(self) -> None:
        mock_model = MagicMock()
        with (
            patch("strands.models.ollama.OllamaModel", return_value=mock_model),
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            TravelAgent()
            MockStrandsAgent.assert_called_once()
            _, kwargs = MockStrandsAgent.call_args
            assert kwargs["system_prompt"] == _SYSTEM_PROMPT

    def test_system_prompt_is_set(self) -> None:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()

        with (
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            TravelAgent(llm_provider=provider)
            _, kwargs = MockStrandsAgent.call_args
            assert "travel advisor" in kwargs["system_prompt"].lower()

    def test_system_prompt_mentions_tool(self) -> None:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()

        with (
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            TravelAgent(llm_provider=provider)
            _, kwargs = MockStrandsAgent.call_args
            assert "get_travel_recommendations" in kwargs["system_prompt"]


# ---------------------------------------------------------------------------
# TravelAgent.run
# ---------------------------------------------------------------------------


class TestTravelAgentRun:
    def _make_agent(self, reply: str = "Great trip ahead!") -> TravelAgent:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()

        mock_strands_result = MagicMock()
        mock_strands_result.__str__ = lambda self: reply

        with (
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            mock_inner = MagicMock(return_value=mock_strands_result)
            MockStrandsAgent.return_value = mock_inner
            agent = TravelAgent(llm_provider=provider)

        # Stub extractor — tests that care about preferences configure it themselves
        agent._extractor = MagicMock()
        agent._extractor.extract.return_value = UserPreferences()

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

        with (
            patch("app.agents.agent.StrandsAgent") as MockStrandsAgent,
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            mock_inner = MagicMock(return_value=mock_strands_result)
            MockStrandsAgent.return_value = mock_inner
            agent = TravelAgent(llm_provider=provider)

        agent._extractor = MagicMock()
        agent._extractor.extract.return_value = UserPreferences()

        agent.run("I love hiking")
        call_arg = agent._agent.call_args[0][0]
        assert "I love hiking" in call_arg

    def test_result_contains_extracted_preferences(self) -> None:
        agent = self._make_agent()
        agent._extractor.extract.return_value = UserPreferences(travel_style="beach", budget="luxury")
        result = agent.run("I want a luxury beach holiday")
        assert result.extracted_preferences.travel_style == "beach"
        assert result.extracted_preferences.budget == "luxury"

    def test_result_contains_recommendations_preview_as_list(self) -> None:
        # recommendations_preview is populated only when the Strands agent calls the tool;
        # with a mocked agent it stays empty — assert the type is correct.
        agent = self._make_agent()
        result = agent.run("adventure hiking trip")
        assert isinstance(result.recommendations_preview, list)

    def test_recommendations_preview_reset_each_run(self) -> None:
        # Manually populate the sink from a previous turn; it must be cleared on the next run.
        agent = self._make_agent()
        agent._last_recommendations.append({"destination": "Stale", "description": "Old data."})
        result = agent.run("new message")
        assert result.recommendations_preview == []

    def test_empty_message_has_no_extracted_preferences(self) -> None:
        agent = self._make_agent()
        result = agent.run("")
        assert result.extracted_preferences == UserPreferences()


# ---------------------------------------------------------------------------
# _build_context_message
# ---------------------------------------------------------------------------


class TestBuildContextMessage:
    def test_contains_user_message(self) -> None:
        prefs = UserPreferences()
        result = _build_context_message("I want to go to Paris", prefs)
        assert "I want to go to Paris" in result

    def test_null_fields_shown_as_unknown(self) -> None:
        prefs = UserPreferences()
        result = _build_context_message("hi", prefs)
        assert "Travel style: not yet known" in result
        assert "Budget: not yet known" in result

    def test_known_fields_shown(self) -> None:
        prefs = UserPreferences(travel_style="beach", budget="luxury")
        result = _build_context_message("hi", prefs)
        assert "Travel style: beach" in result
        assert "Budget: luxury" in result

    def test_list_fields_joined(self) -> None:
        prefs = UserPreferences(preferred_destinations=["Paris", "Tokyo"])
        result = _build_context_message("hi", prefs)
        assert "Paris" in result
        assert "Tokyo" in result

    def test_empty_list_shown_as_unknown(self) -> None:
        prefs = UserPreferences(preferred_destinations=[])
        result = _build_context_message("hi", prefs)
        assert "Preferred destinations: not yet known" in result


# ---------------------------------------------------------------------------
# get_travel_recommendations tool
# ---------------------------------------------------------------------------


class TestGetTravelRecommendationsTool:
    """Tests for the @tool-decorated closure created inside TravelAgent.__init__."""

    @pytest.fixture(autouse=True)
    def agent(self) -> None:
        provider = MagicMock(spec=LLMProvider)
        provider.get_model.return_value = MagicMock()
        with (
            patch("app.agents.agent.StrandsAgent"),
            patch("app.agents.agent.RecommendationsAgent"),
        ):
            self._agent = TravelAgent(llm_provider=provider)
        # Replace the real RecommendationsAgent with a mock after construction
        self._mock_rec_agent = MagicMock(spec=RecommendationsAgent)
        self._agent._recommendations_agent = self._mock_rec_agent

    def _call_tool(self, **kwargs: str) -> str:
        """Invoke the tool function directly (bypassing the Strands dispatch layer)."""
        return self._agent._get_travel_recommendations_tool(**kwargs)

    def test_tool_name_is_get_travel_recommendations(self) -> None:
        assert self._agent._get_travel_recommendations_tool.tool_name == "get_travel_recommendations"

    def test_tool_calls_recommendations_agent(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool(travel_style="beach")
        self._mock_rec_agent.get_recommendations.assert_called_once()

    def test_tool_passes_travel_style(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool(travel_style="adventure")
        prefs = self._mock_rec_agent.get_recommendations.call_args[0][0]
        assert prefs.travel_style == "adventure"

    def test_tool_passes_budget(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool(budget="luxury")
        prefs = self._mock_rec_agent.get_recommendations.call_args[0][0]
        assert prefs.budget == "luxury"

    def test_tool_parses_comma_separated_destinations(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool(preferred_destinations="Japan, Thailand")
        prefs = self._mock_rec_agent.get_recommendations.call_args[0][0]
        assert "Japan" in prefs.preferred_destinations
        assert "Thailand" in prefs.preferred_destinations

    def test_tool_parses_comma_separated_interests(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool(interests="hiking, diving")
        prefs = self._mock_rec_agent.get_recommendations.call_args[0][0]
        assert "hiking" in prefs.interests
        assert "diving" in prefs.interests

    def test_tool_empty_strings_become_none_or_empty_list(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool()
        prefs = self._mock_rec_agent.get_recommendations.call_args[0][0]
        assert prefs.travel_style is None
        assert prefs.budget is None
        assert prefs.preferred_destinations == []
        assert prefs.interests == []

    def test_tool_updates_last_recommendations(self) -> None:
        recs = [{"destination": "Bali, Indonesia", "description": "Stunning beaches."}]
        self._mock_rec_agent.get_recommendations.return_value = recs
        self._call_tool(travel_style="beach")
        assert self._agent._last_recommendations == recs

    def test_tool_clears_previous_recommendations(self) -> None:
        self._agent._last_recommendations.append({"destination": "Stale", "description": "Old."})
        self._mock_rec_agent.get_recommendations.return_value = []
        self._call_tool()
        assert self._agent._last_recommendations == []

    def test_tool_returns_formatted_string(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = [
            {"destination": "Nepal", "description": "Legendary Himalayan trekking."},
        ]
        result = self._call_tool(travel_style="adventure")
        assert "Nepal" in result
        assert "Legendary Himalayan trekking." in result

    def test_tool_returns_no_results_message_when_empty(self) -> None:
        self._mock_rec_agent.get_recommendations.return_value = []
        result = self._call_tool()
        assert "No matching recommendations" in result


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
