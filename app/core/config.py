from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    ENV: Literal["development", "staging", "production"] = "development"
    LLM_PROVIDER: str = "openai"
    VECTOR_STORE: str = "chroma"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
