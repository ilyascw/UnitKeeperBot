from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from dishka.integrations.fastapi import FromDishka, inject

from unitkeeper_backend.application.auth.service import AuthService
from unitkeeper_backend.domain.errors import AuthenticationError

bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def require_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: FromDishka[AuthService] = None,
) -> int:
    if credentials is None:
        raise AuthenticationError("Authorization header is required")
    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Authorization scheme must be Bearer")
    return auth_service.resolve_user_id(credentials.credentials)
