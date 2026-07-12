from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from unitkeeper_backend.application.models import NotificationOutboxEventInfo
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from db.enums import NotificationEventType


class NotificationOutboxService:
    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def list_ready(self, *, limit: int) -> list[NotificationOutboxEventInfo]:
        return await self._uow.notifications.list_ready(now=self._clock.now(), limit=limit)

    async def enqueue_once(
        self,
        *,
        dedupe_key: str,
        correlation_id: str | None,
        event_type: NotificationEventType | str,
        recipient_user_id: int,
        group_id: int | None,
        payload: dict[str, object],
        deep_link_path: str | None,
    ) -> tuple[NotificationOutboxEventInfo, bool]:
        event, created = await self._uow.notifications.enqueue_once(
            dedupe_key=dedupe_key,
            correlation_id=correlation_id,
            event_type=NotificationEventType(event_type),
            recipient_user_id=recipient_user_id,
            group_id=group_id,
            payload=payload,
            deep_link_path=deep_link_path,
        )
        if created:
            await self._uow.commit()
        return event, created

    async def acknowledge(self, *, event_id: UUID) -> NotificationOutboxEventInfo:
        event = await self._uow.notifications.acknowledge(event_id=event_id, acknowledged_at=self._clock.now())
        await self._uow.commit()
        return event

    async def fail(
        self,
        *,
        event_id: UUID,
        error_message: str,
        retry_after_seconds: int | None,
        terminal: bool,
    ) -> NotificationOutboxEventInfo:
        retry_at = None
        if not terminal and retry_after_seconds is not None:
            retry_at = self._clock.now() + timedelta(seconds=retry_after_seconds)
        event = await self._uow.notifications.fail(
            event_id=event_id,
            failed_at=self._clock.now(),
            error_message=error_message,
            retry_at=retry_at,
            terminal=terminal,
        )
        await self._uow.commit()
        return event
