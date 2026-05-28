from __future__ import annotations

from fastapi import Header

from unitkeeper_backend.config import settings
from unitkeeper_backend.domain.errors import AuthenticationError

INTERNAL_AUTH_HEADER = "X-Internal-Auth"


async def require_internal_auth(
    x_internal_auth: str | None = Header(default=None, alias=INTERNAL_AUTH_HEADER),
) -> None:
    expected = settings.internal_bot_secret
    if not expected:
        raise AuthenticationError("Internal transport is disabled")
    if x_internal_auth != expected:
        raise AuthenticationError("Internal auth failed")
