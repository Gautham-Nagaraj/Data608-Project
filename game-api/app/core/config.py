from typing import List
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    DATABASE_URL: PostgresDsn
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["*"]
    SECRET_KEY: str
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

# Initialize settings instance
settings = Settings()
