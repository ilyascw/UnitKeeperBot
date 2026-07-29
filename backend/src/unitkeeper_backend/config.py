from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "UnitKeeper Backend"
    app_env: str = "dev"
    database_url: str = (
        "postgresql+asyncpg://unitkeeper:unitkeeper@127.0.0.1:5432/unitkeeper_common"
    )
    sqlalchemy_echo: bool = False
    telegram_bot_token: str = "change-me"
    telegram_auth_max_age_seconds: int = 86400
    session_secret: str = "change-me-too"
    session_ttl_seconds: int = 86400
    default_timezone: str = "UTC"
    internal_bot_secret: str = ""


settings = Settings()
