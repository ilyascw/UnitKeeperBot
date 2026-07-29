from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from unitkeeper_backend.api.schemas.common import CurrentContextResponse


class TelegramAuthRequest(BaseModel):
    init_data: str


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    context: CurrentContextResponse
