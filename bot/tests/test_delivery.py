from __future__ import annotations

from urllib.parse import urlsplit

import pytest
from aiogram.types import InlineKeyboardMarkup

from unitkeeper_bot.application.notifications import NotificationWorker
from unitkeeper_bot.rendering import NotificationEvent


class FakeBackend:
    def __init__(self, event: NotificationEvent) -> None:
        self.events = [event]
        self.acknowledged: list[str] = []
        self.failed: list[tuple[str, str]] = []

    async def list_notification_outbox(self) -> list[NotificationEvent]:
        return self.events

    async def acknowledge_notification(self, *, event_id: str) -> None:
        self.acknowledged.append(event_id)

    async def fail_notification(
        self,
        *,
        event_id: str,
        error_message: str,
    ) -> None:
        self.failed.append((event_id, error_message))


class FakeBot:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.messages: list[tuple[int, str, InlineKeyboardMarkup | None]] = []

    async def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ) -> object:
        if self.error is not None:
            raise self.error

        self.messages.append((chat_id, text, reply_markup))
        return object()


def approval_event() -> NotificationEvent:
    return NotificationEvent(
        id="event-1",
        event_type="task_approval_requested",
        recipient_user_id=42,
        payload={
            "task_log_id": 123,
            "task_title": "Тестовая задача",
        },
        deep_link_path="/tasks/history",
    )


@pytest.mark.asyncio
async def test_worker_sends_web_app_button_and_preserves_approval_callbacks() -> None:
    backend = FakeBackend(approval_event())
    bot = FakeBot()

    await NotificationWorker(
        backend=backend,  # type: ignore[arg-type]
        bot=bot,  # type: ignore[arg-type]
        miniapp_url="https://app.example",
    ).deliver_ready()

    assert len(bot.messages) == 1
    chat_id, text, markup = bot.messages[0]

    assert chat_id == 42
    assert "Нужна проверка задачи" in text
    assert markup is not None

    callback_row, miniapp_row = markup.inline_keyboard

    assert [button.callback_data for button in callback_row] == [
        "approval:123:approve",
        "approval:123:reject",
    ]

    assert len(miniapp_row) == 1
    open_button = miniapp_row[0]

    assert open_button.url is None
    assert open_button.web_app is not None

    target = urlsplit(open_button.web_app.url)
    assert target.scheme == "https"
    assert target.netloc == "app.example"
    assert target.path == "/tasks/history"

    assert backend.acknowledged == ["event-1"]
    assert backend.failed == []


@pytest.mark.asyncio
async def test_worker_reports_telegram_failure_without_acknowledging() -> None:
    backend = FakeBackend(approval_event())
    bot = FakeBot(RuntimeError("blocked by Telegram"))

    await NotificationWorker(
        backend=backend,  # type: ignore[arg-type]
        bot=bot,  # type: ignore[arg-type]
        miniapp_url="https://app.example",
    ).deliver_ready()

    assert backend.acknowledged == []
    assert backend.failed == [("event-1", "blocked by Telegram")]
