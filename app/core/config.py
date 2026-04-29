from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    ENV: Literal["development", "staging", "production"] = "development"
    LLM_PROVIDER: Literal["ollama", "bedrock"] = "ollama"
    OLLAMA_HOST: str = "http://localhost:11434"
    # Global default Ollama model — used when no per-agent override is set
    OLLAMA_MODEL_ID: str = "llama3.1"
    # Per-agent Ollama overrides (empty string = fall back to OLLAMA_MODEL_ID)
    OLLAMA_MODEL_ID_TRAVEL_AGENT: str = ""
    OLLAMA_MODEL_ID_EXTRACTOR_AGENT: str = ""
    OLLAMA_MODEL_ID_RECOMMENDATIONS_AGENT: str = ""
    # Global default Bedrock model
    BEDROCK_MODEL_ID: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    # Per-agent Bedrock overrides (empty string = fall back to BEDROCK_MODEL_ID)
    BEDROCK_MODEL_ID_TRAVEL_AGENT: str = ""
    BEDROCK_MODEL_ID_EXTRACTOR_AGENT: str = ""
    BEDROCK_MODEL_ID_RECOMMENDATIONS_AGENT: str = ""
    SESSION_STORAGE_DIR: str = "/tmp/travel-agent-sessions"
    DYNAMODB_ENDPOINT_URL: str = "http://localhost:8001"
    DYNAMODB_TABLE_USER_PROFILES: str = "UserProfiles"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "dummy"
    AWS_SECRET_ACCESS_KEY: str = "dummy"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
