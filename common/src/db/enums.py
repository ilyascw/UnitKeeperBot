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
