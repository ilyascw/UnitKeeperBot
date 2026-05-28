from __future__ import annotations

from fastapi import APIRouter, Depends, status

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from db.enums import Weekday

from unitkeeper_backend.api.dependencies.auth import require_user_id
from unitkeeper_backend.api.schemas.common import CurrentContextResponse, GroupResponse
from unitkeeper_backend.api.schemas.groups import (
    CreateGroupRequest,
    GroupCardResponse,
    GroupMembersResponse,
    JoinGroupRequest,
    MemberCardResponse,
    UpdateGroupSettingsRequest,
    UpdateWeightsRequest,
)
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.infrastructure.time import UtcClock

router = APIRouter(prefix="/groups", tags=["groups"], route_class=DishkaRoute)


@router.get("/current", response_model=GroupCardResponse)
async def get_current_group(
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> GroupCardResponse:
    card = await group_service.get_current_group_card(user_id=user_id)
    return GroupCardResponse.model_validate(card, from_attributes=True)


@router.get("/current/summary", response_model=GroupResponse)
async def get_current_group_summary(
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> GroupResponse:
    group = await group_service.get_current_group(user_id=user_id)
    return GroupResponse.model_validate(group, from_attributes=True)


@router.get("/current/members", response_model=GroupMembersResponse)
async def list_current_group_members(
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> GroupMembersResponse:
    members = await group_service.list_current_group_members(user_id=user_id)
    return GroupMembersResponse(
        members=[MemberCardResponse.model_validate(item, from_attributes=True) for item in members],
    )


@router.patch("/current/settings", response_model=GroupResponse)
async def update_current_group_settings(
    request: UpdateGroupSettingsRequest,
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> GroupResponse:
    weekday = Weekday(request.sprint_start_weekday) if request.sprint_start_weekday is not None else None
    group = await group_service.update_current_group_settings(
        user_id=user_id,
        join_secret=request.join_secret,
        sprint_start_weekday=weekday,
        sprint_duration_days=request.sprint_duration_days,
    )
    return GroupResponse.model_validate(group, from_attributes=True)


@router.put("/current/weights", response_model=GroupMembersResponse)
async def update_current_group_weights(
    request: UpdateWeightsRequest,
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> GroupMembersResponse:
    members = await group_service.update_current_group_weights(
        user_id=user_id,
        weights_by_user_id={item.user_id: item.weight_percent for item in request.weights},
    )
    return GroupMembersResponse(
        members=[MemberCardResponse.model_validate(item, from_attributes=True) for item in members],
    )


@router.post("", response_model=CurrentContextResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    request: CreateGroupRequest,
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> CurrentContextResponse:
    context = await group_service.create_group(
        user_id=user_id,
        name=request.name,
        join_secret=request.join_secret,
        sprint_start_weekday=Weekday(request.sprint_start_weekday),
        sprint_duration_days=request.sprint_duration_days,
        timezone=request.timezone,
    )
    return CurrentContextResponse.model_validate(context, from_attributes=True)


@router.post("/join", response_model=CurrentContextResponse)
async def join_group(
    request: JoinGroupRequest,
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
) -> CurrentContextResponse:
    context = await group_service.join_group(
        user_id=user_id,
        group_name=request.name,
        join_secret=request.join_secret,
    )
    return CurrentContextResponse.model_validate(context, from_attributes=True)


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    user_id: int = Depends(require_user_id),
    group_service: FromDishka[GroupService] = None,
    clock: FromDishka[UtcClock] = None,
) -> None:
    await group_service.leave_group(user_id=user_id, left_at=clock.now())
