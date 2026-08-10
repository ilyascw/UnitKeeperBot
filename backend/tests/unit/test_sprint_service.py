from __future__ import annotations

from decimal import Decimal

import pytest
from db.enums import SprintRunStatus, TaskLogStatus, Weekday

from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.application.tasks.service import TaskService
from unitkeeper_backend.domain.errors import BusinessRuleViolation


@pytest.mark.asyncio
async def test_temp_results_and_sprint_close_persist_balances() -> None:
    uow = InMemoryUnitOfWork()
    for user_id in (1, 2):
        uow.users.users[user_id] = UserProfile(
            user_id, f"user{user_id}", f"User {user_id}", None, "en", False
        )
    group_service = GroupService(
        uow=uow,
        context_service=CurrentContextService(uow=uow),
        clock=FakeClock(utc_datetime(2026, 3, 16)),
    )
    await group_service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    await group_service.join_group(user_id=2, group_name="team", join_secret="secret")

    clock = FakeClock(utc_datetime(2026, 3, 16))
    task_service = TaskService(uow=uow, clock=clock)
    sprint_service = SprintService(uow=uow, clock=clock)
    task = await task_service.create_task(
        group_id=1,
        title="Laundry",
        frequency_per_sprint=2,
        unit_cost=Decimal("3.00"),
    )
    pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
    await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)

    results = await sprint_service.get_temp_results(user_id=1, group_id=1)
    assert results.planned_units == Decimal("3.00")
    assert results.completed_units == Decimal("3.00")
    assert results.breakdown[0].title == "Laundry"
    assert results.breakdown[0].performer_user_id == 1
    assert results.breakdown[0].performer_first_name == "User 1"
    assert results.group.planned_units == Decimal("6.00")
    assert results.group.completed_units == Decimal("3.00")
    assert results.group.progress_percent == Decimal("50.00")

    results_for_user2 = await sprint_service.get_temp_results(user_id=2, group_id=1)
    assert results_for_user2.completed_units == Decimal("0.00")
    assert results_for_user2.group.completed_units == Decimal("3.00")
    assert results_for_user2.group.planned_units == Decimal("6.00")
    # Breakdown is group-wide: user2 sees what user1 completed too.
    assert results_for_user2.breakdown[0].title == "Laundry"
    assert results_for_user2.breakdown[0].performer_user_id == 1

    run = await sprint_service.close_current_sprint(group_id=1)
    assert run.status is SprintRunStatus.CLOSED
    assert len(run.member_results) == 2
    assert uow.sprints.transactions

    with pytest.raises(BusinessRuleViolation):
        await sprint_service.close_current_sprint(group_id=1)


@pytest.mark.asyncio
async def test_temp_results_aggregate_by_performer_and_sort_by_latest_completion() -> None:
    uow = InMemoryUnitOfWork()
    for user_id in (1, 2):
        uow.users.users[user_id] = UserProfile(
            user_id, f"user{user_id}", f"User {user_id}", None, "en", False
        )
    group_service = GroupService(
        uow=uow,
        context_service=CurrentContextService(uow=uow),
        clock=FakeClock(utc_datetime(2026, 3, 16)),
    )
    await group_service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    await group_service.join_group(user_id=2, group_name="team", join_secret="secret")

    task_service = TaskService(uow=uow, clock=FakeClock(utc_datetime(2026, 3, 16)))
    older_task = await task_service.create_task(
        group_id=1,
        title="Alpha",
        frequency_per_sprint=2,
        unit_cost=Decimal("2.00"),
    )
    newer_task = await task_service.create_task(
        group_id=1,
        title="Zulu",
        frequency_per_sprint=2,
        unit_cost=Decimal("3.00"),
    )
    await uow.tasks.create_task_log(
        group_id=1,
        task_id=older_task.id,
        performer_user_id=2,
        status=TaskLogStatus.COMPLETED,
        created_at=utc_datetime(2026, 3, 16, 8),
        approver_user_id=1,
        decided_at=utc_datetime(2026, 3, 16, 9),
    )
    await uow.tasks.create_task_log(
        group_id=1,
        task_id=newer_task.id,
        performer_user_id=1,
        status=TaskLogStatus.COMPLETED,
        created_at=utc_datetime(2026, 3, 16, 10),
        approver_user_id=2,
        decided_at=utc_datetime(2026, 3, 16, 11),
    )
    await uow.tasks.create_task_log(
        group_id=1,
        task_id=newer_task.id,
        performer_user_id=1,
        status=TaskLogStatus.COMPLETED,
        created_at=utc_datetime(2026, 3, 16, 12),
        approver_user_id=2,
        decided_at=utc_datetime(2026, 3, 16, 13),
    )
    await uow.tasks.create_task_log(
        group_id=1,
        task_id=older_task.id,
        performer_user_id=1,
        status=TaskLogStatus.COMPLETED,
        created_at=utc_datetime(2026, 3, 16, 11),
        approver_user_id=2,
        decided_at=utc_datetime(2026, 3, 16, 12),
    )

    results = await SprintService(
        uow=uow,
        clock=FakeClock(utc_datetime(2026, 3, 16, 14)),
    ).get_temp_results(user_id=1, group_id=1)

    assert [item.title for item in results.breakdown] == ["Zulu", "Alpha", "Alpha"]
    assert results.breakdown[0].completed_count == 2
    assert results.breakdown[0].performer_user_id == 1
    assert results.breakdown[0].last_completed_at == utc_datetime(2026, 3, 16, 13)
    assert results.breakdown[1].performer_user_id == 1
    assert results.breakdown[1].last_completed_at == utc_datetime(2026, 3, 16, 12)
    assert results.breakdown[2].performer_user_id == 2
    assert results.breakdown[2].last_completed_at == utc_datetime(2026, 3, 16, 9)


@pytest.mark.asyncio
async def test_close_current_sprint_auto_rejects_stale_pending_logs() -> None:
    uow = InMemoryUnitOfWork()
    for user_id in (1, 2):
        uow.users.users[user_id] = UserProfile(
            user_id, f"user{user_id}", f"User {user_id}", None, "en", False
        )
    group_service = GroupService(
        uow=uow,
        context_service=CurrentContextService(uow=uow),
        clock=FakeClock(utc_datetime(2026, 3, 16)),
    )
    await group_service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    await group_service.join_group(user_id=2, group_name="team", join_secret="secret")

    clock = FakeClock(utc_datetime(2026, 3, 16))
    task_service = TaskService(uow=uow, clock=clock)
    sprint_service = SprintService(uow=uow, clock=clock)
    task = await task_service.create_task(
        group_id=1,
        title="Dishes",
        frequency_per_sprint=2,
        unit_cost=Decimal("3.00"),
    )
    pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
    assert pending.status is TaskLogStatus.PENDING

    await sprint_service.close_current_sprint(group_id=1)

    stale_log = await uow.tasks.get_task_log(log_id=pending.id)
    assert stale_log is not None
    assert stale_log.status is TaskLogStatus.REJECTED
    assert stale_log.approver_user_id is None
    assert stale_log.rejection_reason

    with pytest.raises(BusinessRuleViolation):
        await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)
