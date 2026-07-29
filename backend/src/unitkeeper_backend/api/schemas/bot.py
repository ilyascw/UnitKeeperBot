from __future__ import annotations

from uuid import UUID

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


class BotNotificationFailRequest(BaseModel):
    error_message: str = Field(min_length=1, max_length=4000)
    retry_after_seconds: int | None = Field(default=None, ge=0, le=86400)
    terminal: bool = False


class BotNotificationEventResponse(BaseModel):
    id: UUID
    event_type: str
    recipient_user_id: int
    group_id: int | None
    payload: dict[str, object]
    deep_link_path: str | None
    correlation_id: str | None
    attempt_count: int


class BotNotificationOutboxResponse(BaseModel):
    items: list[BotNotificationEventResponse]
