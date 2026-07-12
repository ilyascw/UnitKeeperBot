from __future__ import annotations

from sqlalchemy import Table, UniqueConstraint

from db.enums import (
    IdempotencyStatus,
    NotificationDeliveryAttemptStatus,
    NotificationEventType,
    NotificationOutboxStatus,
)
from db.models import IdempotencyKey, NotificationDeliveryAttempt, NotificationOutboxEvent


def _unique_constraint_columns(table: Table) -> set[frozenset[str]]:
    return {
        frozenset(constraint.columns.keys())
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }


def test_outbox_schema_exposes_delivery_lifecycle() -> None:
    event_columns = NotificationOutboxEvent.__table__.c
    attempt_columns = NotificationDeliveryAttempt.__table__.c

    assert {
        NotificationEventType.TASK_APPROVAL_REQUESTED,
        NotificationEventType.TASK_APPROVED,
        NotificationEventType.TASK_REJECTED,
        NotificationEventType.SPRINT_CLOSED,
        NotificationEventType.REMINDER,
    } <= set(NotificationEventType)
    assert set(NotificationOutboxStatus) == {
        NotificationOutboxStatus.PENDING,
        NotificationOutboxStatus.DELIVERED,
        NotificationOutboxStatus.DEAD_LETTER,
    }
    assert set(NotificationDeliveryAttemptStatus) == {
        NotificationDeliveryAttemptStatus.ACKNOWLEDGED,
        NotificationDeliveryAttemptStatus.FAILED,
    }
    assert {
        "payload",
        "deep_link_path",
        "dedupe_key",
        "correlation_id",
        "next_attempt_at",
        "delivered_at",
        "last_error",
    } <= set(event_columns.keys())
    assert frozenset({"dedupe_key"}) in _unique_constraint_columns(
        NotificationOutboxEvent.__table__
    )
    assert {"attempt_number", "status", "error_message", "acknowledged_at"} <= set(attempt_columns.keys())
    assert frozenset({"event_id", "attempt_number"}) in _unique_constraint_columns(
        NotificationDeliveryAttempt.__table__
    )


def test_idempotency_schema_scopes_keys_and_records_results() -> None:
    columns = IdempotencyKey.__table__.c

    assert set(IdempotencyStatus) == {
        IdempotencyStatus.PROCESSING,
        IdempotencyStatus.COMPLETED,
        IdempotencyStatus.FAILED,
    }
    assert {"request_fingerprint", "response_status_code", "response_payload", "expires_at"} <= set(columns.keys())
    assert frozenset({"scope", "actor_key", "key"}) in _unique_constraint_columns(IdempotencyKey.__table__)
