from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from unitkeeper_bot.backend.client import BackendGateway, BackendTransportError
from unitkeeper_bot.rendering import NotificationEvent as RenderedEvent
from unitkeeper_bot.rendering import render_notification

_logger = logging.getLogger(__name__)


class NotificationWorker:
    """Delivery adapter: it renders backend events and acknowledges the result."""

    def __init__(self, *, backend: BackendGateway, bot: Bot, miniapp_url: str) -> None:
        self._backend = backend
        self._bot = bot
        self._miniapp_url = miniapp_url

    async def deliver_ready(self) -> None:
        try:
            events = await self._backend.list_notification_outbox()
        except BackendTransportError:
            _logger.exception("Unable to fetch notification outbox")
            return
        for event in events:
            rendered = render_notification(
                RenderedEvent(
                    id=event.id,
                    event_type=event.event_type,
                    recipient_user_id=event.recipient_user_id,
                    payload=event.payload,
                    deep_link_path=event.deep_link_path,
                ),
                app_url=self._miniapp_url,
            )
            rows: list[list[InlineKeyboardButton]] = []
            log_id = event.payload.get("task_log_id")
            if event.event_type == "task_approval_requested" and isinstance(log_id, int):
                rows.append(
                    [
                        InlineKeyboardButton(text="Подтвердить", callback_data=f"approval:{log_id}:approve"),
                        InlineKeyboardButton(text="Отклонить", callback_data=f"approval:{log_id}:reject"),
                    ]
                )
            if rendered.miniapp_url and rendered.button_label:
                rows.append([InlineKeyboardButton(text=rendered.button_label, url=rendered.miniapp_url)])
            try:
                await self._bot.send_message(
                    chat_id=event.recipient_user_id,
                    text=rendered.text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=rows) if rows else None,
                )
                await self._backend.acknowledge_notification(event_id=event.id)
            except Exception as error:
                _logger.exception("Unable to deliver notification", extra={"event_id": event.id})
                try:
                    await self._backend.fail_notification(event_id=event.id, error_message=str(error)[:4000])
                except BackendTransportError:
                    _logger.exception("Unable to record notification failure", extra={"event_id": event.id})
