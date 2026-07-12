from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from unitkeeper_bot.rendering import NotificationEvent


class BackendTransportError(Exception):
    """The backend transport could not complete a bot request."""


@dataclass(frozen=True, slots=True)
class TelegramUser:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_bot: bool


@dataclass(frozen=True, slots=True)
class CurrentContext:
    has_active_group: bool


class BackendGateway(Protocol):
    async def ensure_user(self, user: TelegramUser) -> None: ...

    async def get_current_context(self, *, telegram_user_id: int) -> CurrentContext: ...

    async def list_notification_outbox(self) -> list[NotificationEvent]: ...

    async def acknowledge_notification(self, *, event_id: str) -> None: ...

    async def fail_notification(self, *, event_id: str, error_message: str) -> None: ...

    async def approve_task_log(self, *, log_id: int, telegram_user_id: int) -> None: ...

    async def reject_task_log(self, *, log_id: int, telegram_user_id: int, reason: str) -> None: ...


class BackendClient:
    def __init__(
        self,
        *,
        base_url: str,
        internal_secret: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers={"X-Internal-Auth": internal_secret},
            timeout=timeout_seconds,
            transport=transport,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def ensure_user(self, user: TelegramUser) -> None:
        await self._request(
            "POST",
            "internal/bot/users/ensure",
            json={
                "telegram_user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
                "is_bot": user.is_bot,
            },
        )

    async def get_current_context(self, *, telegram_user_id: int) -> CurrentContext:
        payload = await self._request("GET", f"internal/bot/users/{telegram_user_id}/context")
        return CurrentContext(has_active_group=payload.get("group") is not None)

    async def list_notification_outbox(self) -> list[NotificationEvent]:
        payload = await self._request("GET", "internal/bot/notifications/outbox")
        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raise BackendTransportError("Backend returned an invalid notification outbox")
        events: list[NotificationEvent] = []
        for item in raw_items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise BackendTransportError("Backend returned an invalid notification event")
            event_payload = item.get("payload")
            if not isinstance(event_payload, dict):
                raise BackendTransportError("Backend returned an invalid notification payload")
            events.append(
                NotificationEvent(
                    id=item["id"],
                    event_type=str(item.get("event_type", "")),
                    recipient_user_id=int(item.get("recipient_user_id", 0)),
                    payload=event_payload,
                    deep_link_path=item.get("deep_link_path") if isinstance(item.get("deep_link_path"), str) else None,
                    correlation_id=item.get("correlation_id") if isinstance(item.get("correlation_id"), str) else None,
                )
            )
        return events

    async def acknowledge_notification(self, *, event_id: str) -> None:
        await self._request("POST", f"internal/bot/notifications/{event_id}/ack")

    async def fail_notification(self, *, event_id: str, error_message: str) -> None:
        await self._request(
            "POST",
            f"internal/bot/notifications/{event_id}/fail",
            json={"error_message": error_message, "retry_after_seconds": 60},
        )

    async def approve_task_log(self, *, log_id: int, telegram_user_id: int) -> None:
        await self._request("POST", f"internal/bot/task-logs/{log_id}/approve", json={"telegram_user_id": telegram_user_id})

    async def reject_task_log(self, *, log_id: int, telegram_user_id: int, reason: str) -> None:
        await self._request(
            "POST",
            f"internal/bot/task-logs/{log_id}/reject",
            json={"telegram_user_id": telegram_user_id, "reason": reason},
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, object]:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise BackendTransportError("Backend request failed") from error
        payload = response.json()
        if not isinstance(payload, dict):
            raise BackendTransportError("Backend returned an invalid response")
        return payload
