from __future__ import annotations

from datetime import datetime
from uuid import UUID

from db.enums import (
    NotificationDeliveryAttemptStatus,
    NotificationEventType,
    NotificationOutboxStatus,
)
from db.models import NotificationDeliveryAttempt, NotificationOutboxEvent
from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from unitkeeper_backend.application.models import NotificationOutboxEventInfo
from unitkeeper_backend.domain.errors import NotFoundError


def _map_event(model: NotificationOutboxEvent) -> NotificationOutboxEventInfo:
    return NotificationOutboxEventInfo(
        id=model.id,
        event_type=model.event_type,
        recipient_user_id=model.recipient_user_id,
        group_id=model.group_id,
        payload=dict(model.payload),
        deep_link_path=model.deep_link_path,
        correlation_id=model.correlation_id,
        status=model.status,
        attempt_count=model.attempt_count,
        next_attempt_at=model.next_attempt_at,
        delivered_at=model.delivered_at,
        last_error=model.last_error,
        created_at=model.created_at,
    )


class SqlAlchemyNotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def enqueue(
        self,
        *,
        event_type: NotificationEventType,
        recipient_user_id: int,
        group_id: int | None,
        payload: dict[str, object],
        deep_link_path: str | None,
    ) -> NotificationOutboxEventInfo:
        model = NotificationOutboxEvent(
            event_type=event_type,
            recipient_user_id=recipient_user_id,
            group_id=group_id,
            payload=payload,
            deep_link_path=deep_link_path,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _map_event(model)

    async def enqueue_once(
        self,
        *,
        dedupe_key: str,
        correlation_id: str | None,
        event_type: NotificationEventType,
        recipient_user_id: int,
        group_id: int | None,
        payload: dict[str, object],
        deep_link_path: str | None,
    ) -> tuple[NotificationOutboxEventInfo, bool]:
        statement = (
            insert(NotificationOutboxEvent)
            .values(
                event_type=event_type,
                recipient_user_id=recipient_user_id,
                group_id=group_id,
                payload=payload,
                deep_link_path=deep_link_path,
                dedupe_key=dedupe_key,
                correlation_id=correlation_id,
            )
            .on_conflict_do_nothing(index_elements=["dedupe_key"])
            .returning(NotificationOutboxEvent.id)
        )
        result = await self._session.execute(statement)
        event_id = result.scalar_one_or_none()
        created = event_id is not None
        if event_id is None:
            event_id = await self._session.scalar(
                select(NotificationOutboxEvent.id).where(
                    NotificationOutboxEvent.dedupe_key == dedupe_key
                )
            )
        if event_id is None:
            raise NotFoundError("Notification event was not found after idempotent enqueue")
        event = await self._require_event(event_id)
        return _map_event(event), created

    async def list_ready(self, *, now: datetime, limit: int) -> list[NotificationOutboxEventInfo]:
        query = (
            select(NotificationOutboxEvent)
            .where(
                NotificationOutboxEvent.status == NotificationOutboxStatus.PENDING,
                or_(
                    NotificationOutboxEvent.next_attempt_at.is_(None),
                    NotificationOutboxEvent.next_attempt_at <= now,
                ),
            )
            .order_by(NotificationOutboxEvent.created_at.asc(), NotificationOutboxEvent.id.asc())
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [_map_event(item) for item in result.scalars().all()]

    async def acknowledge(
        self, *, event_id: UUID, acknowledged_at: datetime
    ) -> NotificationOutboxEventInfo:
        event = await self._require_event(event_id)
        if event.status is NotificationOutboxStatus.DELIVERED:
            return _map_event(event)
        event.attempt_count += 1
        event.last_attempt_at = acknowledged_at
        event.delivered_at = acknowledged_at
        event.next_attempt_at = None
        event.last_error = None
        event.status = NotificationOutboxStatus.DELIVERED
        self._session.add(
            NotificationDeliveryAttempt(
                event_id=event.id,
                attempt_number=event.attempt_count,
                status=NotificationDeliveryAttemptStatus.ACKNOWLEDGED,
                acknowledged_at=acknowledged_at,
            )
        )
        await self._session.flush()
        return _map_event(event)

    async def fail(
        self,
        *,
        event_id: UUID,
        failed_at: datetime,
        error_message: str,
        retry_at: datetime | None,
        terminal: bool,
    ) -> NotificationOutboxEventInfo:
        event = await self._require_event(event_id)
        if event.status is NotificationOutboxStatus.DELIVERED:
            return _map_event(event)
        event.attempt_count += 1
        event.last_attempt_at = failed_at
        event.last_error = error_message
        event.next_attempt_at = None if terminal else retry_at
        event.status = (
            NotificationOutboxStatus.DEAD_LETTER if terminal else NotificationOutboxStatus.PENDING
        )
        self._session.add(
            NotificationDeliveryAttempt(
                event_id=event.id,
                attempt_number=event.attempt_count,
                status=NotificationDeliveryAttemptStatus.FAILED,
                error_message=error_message,
            )
        )
        await self._session.flush()
        return _map_event(event)

    async def _require_event(self, event_id: UUID) -> NotificationOutboxEvent:
        event = await self._session.get(NotificationOutboxEvent, event_id)
        if event is None:
            raise NotFoundError("Notification event was not found")
        return event
