"""Application configuration."""

import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    database_url: str = (
        "postgresql+asyncpg://midinecromancer:midinecromancer@localhost:5432/midinecromancer"
    )
    environment: str = "development"
    debug: bool = True
    # Don't read CORS_ORIGINS from env directly - parse it manually
    _cors_origins_env: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins, parsing from environment if set."""
        if self._cors_origins_env:
            origins = [
                origin.strip() for origin in self._cors_origins_env.split(",") if origin.strip()
            ]
            if origins:
                return origins
        # Check environment variable directly
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env:
            origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
            if origins:
                return origins
        # Default
        return ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
