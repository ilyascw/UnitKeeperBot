from __future__ import annotations

from db.models import Group, GroupMembership, SprintMemberResult, SprintRun, Task, TaskLog, User

from unitkeeper_backend.application.models import (
    GroupInfo,
    MembershipInfo,
    SprintMemberResultInfo,
    SprintRunInfo,
    TaskInfo,
    TaskLogInfo,
    UserProfile,
)


def map_user(model: User) -> UserProfile:
    return UserProfile(
        id=model.id,
        username=model.username,
        first_name=model.first_name,
        last_name=model.last_name,
        language_code=model.language_code,
        is_bot=model.is_bot,
    )


def map_membership(model: GroupMembership) -> MembershipInfo:
    return MembershipInfo(
        id=model.id,
        group_id=model.group_id,
        user_id=model.user_id,
        left_at=model.left_at,
        weight_percent=model.weight.weight_percent if model.weight is not None else None,
    )


def map_group(model: Group) -> GroupInfo:
    active_members = [map_membership(item) for item in model.memberships if item.left_at is None]
    return GroupInfo(
        id=model.id,
        name=model.name,
        join_secret=model.join_secret,
        owner_user_id=model.owner_user_id,
        sprint_start_weekday=model.sprint_start_weekday,
        sprint_duration_days=model.sprint_duration_days,
        timezone=model.timezone,
        balance=model.balance,
        created_at=model.created_at.date(),
        active_members=active_members,
    )


def map_task(model: Task) -> TaskInfo:
    return TaskInfo(
        id=model.id,
        group_id=model.group_id,
        title=model.title,
        frequency_per_sprint=model.frequency_per_sprint,
        unit_cost=model.unit_cost,
        deleted_at=model.deleted_at,
    )


def map_task_log(model: TaskLog) -> TaskLogInfo:
    return TaskLogInfo(
        id=model.id,
        group_id=model.group_id,
        task_id=model.task_id,
        performer_user_id=model.performer_user_id,
        status=model.status,
        approver_user_id=model.approver_user_id,
        decided_at=model.decided_at,
        rejection_reason=model.rejection_reason,
        created_at=model.created_at,
    )


def map_sprint_member_result(model: SprintMemberResult) -> SprintMemberResultInfo:
    return SprintMemberResultInfo(
        user_id=model.user_id,
        planned_units=model.planned_units,
        completed_units=model.completed_units,
        efficiency_percent=model.efficiency_percent,
        bonus_units=model.bonus_units,
        balance_delta=model.balance_delta,
        balance_after=model.balance_after,
    )


def map_sprint_run(model: SprintRun) -> SprintRunInfo:
    return SprintRunInfo(
        id=model.id,
        group_id=model.group_id,
        period_start=model.period_start,
        period_end=model.period_end,
        status=model.status,
        total_planned_units=model.total_planned_units,
        total_completed_units=model.total_completed_units,
        bonus_units=model.bonus_units,
        balance_delta=model.balance_delta,
        closed_at=model.closed_at,
        member_results=[map_sprint_member_result(item) for item in model.member_results],
    )
