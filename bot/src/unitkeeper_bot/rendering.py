"""Rendering of backend-owned notification events for Telegram.

This module deliberately accepts presentation-ready values from the backend. It
does not read the database or reproduce sprint, balance, or reminder rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Mapping
from urllib.parse import urlencode


@dataclass(frozen=True, slots=True)
class NotificationEvent:
    """The bot-facing subset of one backend outbox event."""

    id: str
    event_type: str
    recipient_user_id: int
    payload: Mapping[str, object]
    deep_link_path: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True, slots=True)
class RenderedNotification:
    text: str
    miniapp_url: str | None
    button_label: str | None


def _text(payload: Mapping[str, object], name: str, fallback: str = "") -> str:
    value = payload.get(name, fallback)
    return escape(str(value))


def miniapp_url(*, app_url: str, path: str | None, event_id: str) -> str:
    """Attach the event id for tracing without trusting a backend path as URL."""
    base = app_url.rstrip("/")
    normalized_path = path if path and path.startswith("/") else "/"
    return f"{base}{normalized_path}?{urlencode({'notification': event_id})}"


def render_notification(event: NotificationEvent, *, app_url: str) -> RenderedNotification:
    """Turn a backend event into Telegram-safe copy and one optional deep link."""
    payload = event.payload
    task_title = _text(payload, "task_title", "задача")
    group_name = _text(payload, "group_name", "группа")

    kind = str(payload.get("kind", event.event_type))
    match kind:
        case "task_approval_requested":
            text = f"<b>Нужна проверка задачи</b>\n{task_title} отмечена как выполненная."
            label = "Открыть подтверждения"
        case "task_approved":
            text = f"<b>Задача подтверждена</b>\n{task_title} засчитана."
            label = "Открыть историю"
        case "task_rejected":
            text = f"<b>Задача отклонена</b>\n{task_title}\nПричина: {_text(payload, 'rejection_reason', 'не указана')}"
            label = "Открыть историю"
        case "sprint_personal_report":
            text = (
                f"<b>Итоги спринта</b>\n{_text(payload, 'period', 'Спринт завершён')}\n\n"
                f"План: <b>{_text(payload, 'planned_units', '0')}</b> ю\n"
                f"Выполнено: <b>{_text(payload, 'completed_units', '0')}</b> ю\n"
                f"Изменение баланса: <b>{_text(payload, 'balance_delta', '0')}</b> ю"
            )
            label = "Открыть результаты"
        case "sprint_owner_summary":
            text = (
                f"<b>Спринт в группе «{group_name}» закрыт</b>\n"
                f"{_text(payload, 'period', '')}\n\n"
                f"План группы: <b>{_text(payload, 'planned_units', '0')}</b> ю\n"
                f"Выполнено: <b>{_text(payload, 'completed_units', '0')}</b> ю"
            )
            label = "Открыть результаты"
        case "pending_approval_reminder":
            text = f"<b>Есть отметки на подтверждении</b>\n{_text(payload, 'count', '1')} шт. ждут вашего решения."
            label = "Проверить отметки"
        case "sprint_deadline_reminder":
            text = f"<b>Спринт скоро завершится</b>\nДо конца: {_text(payload, 'deadline', 'совсем скоро')}."
            label = "Открыть задачи"
        case "membership_event" | "group_event":
            text = f"<b>Обновление в группе «{group_name}»</b>\n{_text(payload, 'message', 'Состав группы изменился.')}"
            label = "Открыть группу"
        case _:
            text = _text(payload, "message", "У вас новое событие в UnitKeeper.")
            label = "Открыть UnitKeeper"

    return RenderedNotification(
        text=text,
        miniapp_url=miniapp_url(app_url=app_url, path=event.deep_link_path, event_id=event.id),
        button_label=label,
    )
