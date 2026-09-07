"""Application settings, loaded from the environment."""

from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Protune API"
    version: str = "0.1.0"
    environment: str = "development"

    # Comma-separated list of origins allowed to call this API.
    cors_origins: str = "http://localhost:3000"

    gemini_api_key: str = ""
    gemini_model: str = "models/gemini-flash-lite-latest"

    demo_daily_limit: int = 3
    ip_hash_salt: str = "change-me"

    @model_validator(mode="before")
    @classmethod
    def _treat_blank_as_unset(cls, values: Any) -> Any:
        """Ignore environment variables that are present but empty.

        Hosting dashboards happily save a variable with a blank value. Without
        this, a blank `DEMO_DAILY_LIMIT` overrides the default, fails int
        parsing, and takes the entire application down at import time — a 500
        on every route because one optional tuning knob was left empty.
        """
        if isinstance(values, dict):
            return {key: value for key, value in values.items() if value != ""}
        return values

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Annotated rather than a default argument: a call in a default trips ruff B008.
SettingsDep = Annotated[Settings, Depends(get_settings)]
