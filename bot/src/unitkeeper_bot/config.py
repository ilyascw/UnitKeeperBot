from __future__ import annotations

from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="UNITKEEPER_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    bot_token: SecretStr
    backend_base_url: AnyHttpUrl
    internal_bot_secret: SecretStr
    miniapp_url: AnyHttpUrl
    request_timeout_seconds: float = 10.0
