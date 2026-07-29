from __future__ import annotations

from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.models import SessionInfo
from unitkeeper_backend.application.ports import (
    Clock,
    SessionTokenManager,
    TelegramInitDataVerifier,
    UnitOfWork,
)


class AuthService:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        verifier: TelegramInitDataVerifier,
        token_manager: SessionTokenManager,
        clock: Clock,
        context_service: CurrentContextService,
    ) -> None:
        self._uow = uow
        self._verifier = verifier
        self._token_manager = token_manager
        self._clock = clock
        self._context_service = context_service

    async def authenticate(self, init_data: str) -> SessionInfo:
        identity = self._verifier.verify(init_data)
        user = await self._uow.users.upsert_from_telegram(identity)
        await self._uow.commit()
        issued_at = self._clock.now()
        token, expires_at = self._token_manager.issue(user_id=user.id, issued_at=issued_at)
        context = await self._context_service.resolve(user.id)
        return SessionInfo(access_token=token, expires_at=expires_at, context=context)

    def resolve_user_id(self, token: str) -> int:
        return self._token_manager.verify(token)
