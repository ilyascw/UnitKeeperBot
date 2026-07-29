from __future__ import annotations

import pytest

from unitkeeper_bot.application.delivery import NotificationDeliveryWorker
from unitkeeper_bot.rendering import NotificationEvent


class FakeBackend:
    def __init__(self) -> None:
        self.events = [
            NotificationEvent(
                id="event-1",
                event_type="pending_approval_reminder",
                recipient_user_id=42,
                payload={"count": 2},
                deep_link_path="/tasks/history",
            )
        ]
        self.acknowledged: list[tuple[str, str]] = []
        self.failed: list[tuple[str, str, str]] = []

    async def list_notification_outbox(self) -> list[NotificationEvent]:
        return self.events

    async def acknowledge_notification(self, *, event_id: str) -> None:
        self.acknowledged.append((event_id, "worker"))

    async def fail_notification(self, *, event_id: str, error_message: str) -> None:
        self.failed.append((event_id, error_message, "worker"))


class FakeSender:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.messages: list[tuple[int, str]] = []

    async def send_message(self, chat_id: int, text: str, **kwargs: object) -> object:
        if self.error:
            raise self.error
        assert kwargs["parse_mode"] == "HTML"
        self.messages.append((chat_id, text))
        return object()


@pytest.mark.asyncio
async def test_worker_acks_delivered_event_with_same_correlation_id() -> None:
    backend = FakeBackend()
    sender = FakeSender()

    delivered = await NotificationDeliveryWorker(
        backend=backend, sender=sender, miniapp_url="https://app.example"
    ).deliver_once(correlation_id="job-123")

    assert delivered == 1
    assert sender.messages[0][0] == 42
    assert backend.acknowledged == [("event-1", "worker")]
    assert backend.failed == []


@pytest.mark.asyncio
async def test_worker_reports_failed_delivery_without_acknowledging() -> None:
    backend = FakeBackend()
    sender = FakeSender(RuntimeError("blocked by Telegram"))

    delivered = await NotificationDeliveryWorker(
        backend=backend, sender=sender, miniapp_url="https://app.example"
    ).deliver_once(correlation_id="job-456")

    assert delivered == 0
    assert backend.acknowledged == []
    assert backend.failed == [("event-1", "blocked by Telegram", "worker")]
