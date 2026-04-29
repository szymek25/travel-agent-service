from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    ENV: Literal["development", "staging", "production"] = "development"
    LLM_PROVIDER: Literal["ollama", "bedrock"] = "ollama"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL_ID: str = "llama3.1"
    BEDROCK_MODEL_ID: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    VECTOR_STORE: str = "chroma"
    DYNAMODB_ENDPOINT_URL: str = "http://localhost:8001"
    DYNAMODB_TABLE_USER_PROFILES: str = "UserProfiles"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "dummy"
    AWS_SECRET_ACCESS_KEY: str = "dummy"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
