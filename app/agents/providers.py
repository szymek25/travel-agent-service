from abc import ABC, abstractmethod
from typing import Any

# Valid agent names used to look up per-agent model overrides in settings.
# Format: settings.OLLAMA_MODEL_ID_<NAME> / settings.BEDROCK_MODEL_ID_<NAME>
AgentName = str  # "travel_agent" | "extractor_agent" | "recommendations_agent"


class LLMProvider(ABC):
    @abstractmethod
    def get_model(self) -> Any:
        """Return a Strands-compatible model instance."""
        ...


class OllamaProvider(LLMProvider):
    def __init__(self, host: str | None = None, model_id: str | None = None) -> None:
        from app.core.config import settings

        self.host = host or settings.OLLAMA_HOST
        self.model_id = model_id or settings.OLLAMA_MODEL_ID

    def get_model(self) -> Any:
        from strands.models.ollama import OllamaModel

        return OllamaModel(host=self.host, model_id=self.model_id)


class BedrockProvider(LLMProvider):
    def __init__(self, model_id: str | None = None, region_name: str | None = None) -> None:
        from app.core.config import settings

        self.model_id = model_id or settings.BEDROCK_MODEL_ID
        self.region_name = region_name or settings.AWS_REGION

    def get_model(self) -> Any:
        from strands.models import BedrockModel

        return BedrockModel(model_id=self.model_id, region_name=self.region_name)


def create_provider(agent_name: AgentName) -> LLMProvider:
    """Return an LLMProvider for *agent_name*.

    The backend (Ollama vs Bedrock) is determined by ``settings.LLM_PROVIDER``.
    The model used is the per-agent override (e.g. ``OLLAMA_MODEL_ID_TRAVEL_AGENT``)
    when set, otherwise the global default (``OLLAMA_MODEL_ID`` / ``BEDROCK_MODEL_ID``).
    """
    from app.core.config import settings

    suffix = agent_name.upper()  # e.g. "TRAVEL_AGENT"

    if settings.LLM_PROVIDER == "bedrock":
        model_id = getattr(settings, f"BEDROCK_MODEL_ID_{suffix}", "") or settings.BEDROCK_MODEL_ID
        return BedrockProvider(model_id=model_id)

    # Default: ollama
    model_id = getattr(settings, f"OLLAMA_MODEL_ID_{suffix}", "") or settings.OLLAMA_MODEL_ID
    return OllamaProvider(model_id=model_id)
