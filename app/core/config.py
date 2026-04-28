from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    ENV: Literal["development", "staging", "production"] = "development"
    LLM_PROVIDER: str = "openai"
    VECTOR_STORE: str = "chroma"
    DYNAMODB_ENDPOINT_URL: str = "http://localhost:8001"
    DYNAMODB_TABLE_USER_PROFILES: str = "UserProfiles"
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = "dummy"
    AWS_SECRET_ACCESS_KEY: str = "dummy"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
