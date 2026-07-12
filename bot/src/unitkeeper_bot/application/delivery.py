"""Outbox delivery worker; event creation, retries, and state stay in backend."""

from __future__ import annotations

import logging
from typing import Protocol

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from unitkeeper_bot.rendering import NotificationEvent, render_notification

_logger = logging.getLogger(__name__)


class OutboxGateway(Protocol):
    async def list_notification_outbox(self) -> list[NotificationEvent]: ...

    async def acknowledge_notification(self, *, event_id: str) -> None: ...

    async def fail_notification(self, *, event_id: str, error_message: str) -> None: ...


class TelegramSender(Protocol):
    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_markup: InlineKeyboardMarkup | None = None,
        parse_mode: str | None = None,
    ) -> object: ...


class NotificationDeliveryWorker:
    """Send claimed events exactly once per backend claim and report the outcome."""

    def __init__(self, *, backend: OutboxGateway, sender: TelegramSender, miniapp_url: str) -> None:
        self._backend = backend
        self._sender = sender
        self._miniapp_url = miniapp_url

    async def deliver_once(self, *, correlation_id: str, limit: int = 20) -> int:
        events = (await self._backend.list_notification_outbox())[:limit]
        delivered = 0
        for event in events:
            rendered = render_notification(event, app_url=self._miniapp_url)
            markup = _keyboard(rendered.miniapp_url, rendered.button_label)
            try:
                await self._sender.send_message(
                    event.recipient_user_id,
                    rendered.text,
                    reply_markup=markup,
                    parse_mode="HTML",
                )
            except Exception as error:  # Telegram client exceptions are intentionally reported to backend.
                _logger.warning(
                    "Notification delivery failed",
                    extra={"event_id": event.id, "correlation_id": correlation_id},
                    exc_info=error,
                )
                await self._backend.fail_notification(event_id=event.id, error_message=str(error))
                continue
            await self._backend.acknowledge_notification(event_id=event.id)
            delivered += 1
        return delivered


def _keyboard(url: str | None, label: str | None) -> InlineKeyboardMarkup | None:
    if url is None or label is None:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, web_app=WebAppInfo(url=url))]],
    )
