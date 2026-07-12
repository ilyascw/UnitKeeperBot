from __future__ import annotations

import pytest

from unitkeeper_bot.application.start import StartService
from unitkeeper_bot.backend.client import CurrentContext, TelegramUser


class FakeBackend:
    def __init__(self) -> None:
        self.ensured_user: TelegramUser | None = None

    async def ensure_user(self, user: TelegramUser) -> None:
        self.ensured_user = user

    async def get_current_context(self, *, telegram_user_id: int) -> CurrentContext:
        assert telegram_user_id == 12
        return CurrentContext(has_active_group=True)


@pytest.mark.asyncio
async def test_start_initializes_user_only_through_backend() -> None:
    backend = FakeBackend()
    user = TelegramUser(12, "alice", "Alice", None, "en", False)

    context = await StartService(backend=backend).initialize_user(user)

    assert backend.ensured_user == user
    assert context.has_active_group is True
