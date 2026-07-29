from __future__ import annotations

from decimal import Decimal

import pytest
from db.enums import SprintRunStatus, Weekday

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

    run = await sprint_service.close_current_sprint(group_id=1)
    assert run.status is SprintRunStatus.CLOSED
    assert len(run.member_results) == 2
    assert uow.sprints.transactions

    with pytest.raises(BusinessRuleViolation):
        await sprint_service.close_current_sprint(group_id=1)
