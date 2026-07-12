from __future__ import annotations

from decimal import Decimal

import pytest

from db.enums import Weekday
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.jobs.sprint_close import SprintCloseRunner, list_due_group_ids
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.application.tasks.service import TaskService
from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime


async def _build_group(uow: InMemoryUnitOfWork, *, clock: FakeClock) -> None:
    for user_id in (1, 2):
        uow.users.users[user_id] = UserProfile(user_id, f"user{user_id}", f"User {user_id}", None, "en", False)
    group_service = GroupService(uow=uow, context_service=CurrentContextService(uow=uow), clock=clock)
    await group_service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    await group_service.join_group(user_id=2, group_name="team", join_secret="secret")
    task_service = TaskService(uow=uow, clock=clock)
    task = await task_service.create_task(group_id=1, title="Laundry", frequency_per_sprint=2, unit_cost=Decimal("3.00"))
    pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
    await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)


@pytest.mark.asyncio
async def test_list_due_group_ids_only_includes_groups_whose_window_ends_today() -> None:
    uow = InMemoryUnitOfWork()
    mid_sprint_clock = FakeClock(utc_datetime(2026, 3, 16))  # Monday, sprint just started
    await _build_group(uow, clock=mid_sprint_clock)

    assert await list_due_group_ids(uow=uow, clock=mid_sprint_clock) == []

    last_day_clock = FakeClock(utc_datetime(2026, 3, 22))  # Sunday, last day of the 7-day window
    assert await list_due_group_ids(uow=uow, clock=last_day_clock) == [1]

    next_window_clock = FakeClock(utc_datetime(2026, 3, 23))  # Monday, new window has begun
    assert await list_due_group_ids(uow=uow, clock=next_window_clock) == []


@pytest.mark.asyncio
async def test_sprint_close_runner_closes_once_and_skips_duplicate_close(caplog: pytest.LogCaptureFixture) -> None:
    uow = InMemoryUnitOfWork()
    clock = FakeClock(utc_datetime(2026, 3, 22))
    await _build_group(uow, clock=clock)
    sprint_service = SprintService(uow=uow, clock=clock)
    runner = SprintCloseRunner(sprint_service=sprint_service, uow=uow)

    with caplog.at_level("INFO"):
        closed = await runner.close_due_sprint(group_id=1, correlation_id="close-1")
    assert closed is not None
    assert closed.group_id == 1
    assert len(closed.reports) == 2
    assert "sprint_close.closed" in caplog.text

    caplog.clear()
    with caplog.at_level("INFO"):
        repeated = await runner.close_due_sprint(group_id=1, correlation_id="close-2")
    assert repeated is None
    assert "sprint_close.duplicate_skipped" in caplog.text


@pytest.mark.asyncio
async def test_sprint_close_runner_skips_unknown_group() -> None:
    uow = InMemoryUnitOfWork()
    clock = FakeClock(utc_datetime(2026, 3, 22))
    sprint_service = SprintService(uow=uow, clock=clock)
    runner = SprintCloseRunner(sprint_service=sprint_service, uow=uow)

    result = await runner.close_due_sprint(group_id=999, correlation_id="close-missing")
    assert result is None
