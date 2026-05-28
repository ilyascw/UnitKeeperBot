from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    join_secret: str = Field(min_length=3, max_length=255)
    sprint_start_weekday: str
    sprint_duration_days: int = Field(gt=0)
    timezone: str = Field(min_length=1, max_length=64, default="UTC")


class JoinGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    join_secret: str = Field(min_length=3, max_length=255)


class UpdateGroupSettingsRequest(BaseModel):
    join_secret: str | None = Field(default=None, min_length=3, max_length=255)
    sprint_start_weekday: str | None = None
    sprint_duration_days: int | None = Field(default=None, gt=0)


class MemberWeightInput(BaseModel):
    user_id: int
    weight_percent: Decimal


class UpdateWeightsRequest(BaseModel):
    weights: list[MemberWeightInput] = Field(min_length=1)


class MemberCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    weight_percent: Decimal
    balance: Decimal
    is_owner: bool


class GroupCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    owner_user_id: int
    sprint_start_weekday: str
    sprint_duration_days: int
    timezone: str
    group_balance: Decimal
    sprint_period_start: date
    sprint_period_end: date
    sprint_ends_at: datetime
    members: list[MemberCardResponse]
    join_secret: str | None = None


class GroupMembersResponse(BaseModel):
    members: list[MemberCardResponse]
