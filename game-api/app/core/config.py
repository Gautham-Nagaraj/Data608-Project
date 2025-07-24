from pydantic import BaseSettings, PostgresDsn
from typing import List

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    DATABASE_URL: PostgresDsn
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["*"]
    SECRET_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Initialize settings instance
settings = Settings()