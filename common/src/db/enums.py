from __future__ import annotations

import enum


class Weekday(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TaskLogStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"


class SprintRunStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class BalanceTransactionType(str, enum.Enum):
    TRANSFER = "transfer"
    SPRINT_SETTLEMENT = "sprint_settlement"
    SPRINT_BONUS = "sprint_bonus"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class NotificationEventType(str, enum.Enum):
    TASK_APPROVAL_REQUESTED = "task_approval_requested"
    TASK_APPROVED = "task_approved"
    TASK_REJECTED = "task_rejected"
    SPRINT_CLOSED = "sprint_closed"
    REMINDER = "reminder"


class NotificationOutboxStatus(str, enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    DEAD_LETTER = "dead_letter"


class NotificationDeliveryAttemptStatus(str, enum.Enum):
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


class IdempotencyStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
