from abc import ABC, abstractmethod
from typing import Any


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
