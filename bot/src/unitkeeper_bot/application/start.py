from __future__ import annotations

from unitkeeper_bot.backend.client import BackendGateway, CurrentContext, TelegramUser


class StartService:
    def __init__(self, *, backend: BackendGateway) -> None:
        self._backend = backend

    async def initialize_user(self, user: TelegramUser) -> CurrentContext:
        await self._backend.ensure_user(user)
        return await self._backend.get_current_context(telegram_user_id=user.id)
