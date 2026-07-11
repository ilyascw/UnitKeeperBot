from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    code: str
    message: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    language_code: str | None
    is_bot: bool


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    user_id: int
    left_at: datetime | None
    weight_percent: Decimal | None


class GroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_user_id: int
    sprint_start_weekday: str
    sprint_duration_days: int
    timezone: str
    balance: Decimal
    active_members: list[MembershipResponse]


class CurrentContextResponse(BaseModel):
    user: UserResponse
    membership: MembershipResponse | None
    group: GroupResponse | None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    title: str
    frequency_per_sprint: int
    unit_cost: Decimal
    deleted_at: datetime | None
    completed_in_sprint: int
    remaining_in_sprint: int
    pending_in_sprint: int
    available_in_sprint: int


class TaskLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    task_id: int
    performer_user_id: int
    status: str
    approver_user_id: int | None
    decided_at: datetime | None
    rejection_reason: str | None
    created_at: datetime


class CompletedTaskBreakdownResponse(BaseModel):
    task_id: int
    title: str
    completed_count: int
    completed_units: Decimal


class TempResultsResponse(BaseModel):
    period_start: date
    period_end: date
    planned_units: Decimal
    completed_units: Decimal
    progress_percent: Decimal
    breakdown: list[CompletedTaskBreakdownResponse]


class SprintMemberResultResponse(BaseModel):
    user_id: int
    planned_units: Decimal
    completed_units: Decimal
    efficiency_percent: Decimal
    bonus_units: Decimal
    balance_delta: Decimal
    balance_after: Decimal


class SprintRunResponse(BaseModel):
    id: int
    group_id: int
    period_start: date
    period_end: date
    status: str
    total_planned_units: Decimal
    total_completed_units: Decimal
    bonus_units: Decimal
    balance_delta: Decimal
    closed_at: datetime | None
    member_results: list[SprintMemberResultResponse]
