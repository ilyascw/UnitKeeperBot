from __future__ import annotations

from pydantic import BaseModel, Field


class EnsureUserRequest(BaseModel):
    telegram_user_id: int = Field(gt=0)
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_bot: bool = False


class BotApproveRequest(BaseModel):
    telegram_user_id: int = Field(gt=0)


class BotRejectRequest(BaseModel):
    telegram_user_id: int = Field(gt=0)
    reason: str = Field(min_length=1)
