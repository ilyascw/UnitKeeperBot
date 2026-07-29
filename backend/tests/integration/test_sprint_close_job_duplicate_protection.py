"""Integration-level coverage for issue-06: rerunning the sprint-close job must
not double-close (or double-pay) the same sprint period.

This exercises the full application-layer pipeline together (discovery via
``list_due_group_ids``, close via the real ``SprintService.close_current_sprint``
through ``SprintCloseRunner``, and report fan-out via ``SprintCloseJob`` +
``SprintReportPublisher``) rather than mocking any of the collaborators, so it
proves the pieces are wired correctly end to end and not just individually.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from db.enums import Weekday

from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.jobs.notifications import SprintReportPublisher
from unitkeeper_backend.application.jobs.scheduler import SprintCloseJob
from unitkeeper_backend.application.jobs.sprint_close import SprintCloseRunner, list_due_group_ids
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.application.tasks.service import TaskService


class RecordingPublisher:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.keys: set[str] = set()

    async def enqueue_once(self, **kwargs: object) -> None:
        key = str(kwargs["dedupe_key"])
        if key in self.keys:
            return
        self.keys.add(key)
        self.calls.append(kwargs)


async def _seed_group(uow: InMemoryUnitOfWork, *, clock: FakeClock) -> None:
    for user_id in (1, 2):
        uow.users.users[user_id] = UserProfile(
            user_id, f"user{user_id}", f"User {user_id}", None, "en", False
        )
    group_service = GroupService(
        uow=uow, context_service=CurrentContextService(uow=uow), clock=clock
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
    task_service = TaskService(uow=uow, clock=clock)
    task = await task_service.create_task(
        group_id=1, title="Laundry", frequency_per_sprint=2, unit_cost=Decimal("3.00")
    )
    pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
    await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)


@pytest.mark.asyncio
async def test_rerunning_scheduler_pass_does_not_double_close_or_double_pay() -> None:
    uow = InMemoryUnitOfWork()
    clock = FakeClock(utc_datetime(2026, 3, 22))  # Sunday: last day of the sprint window
    await _seed_group(uow, clock=clock)

    sprint_service = SprintService(uow=uow, clock=clock)
    closer = SprintCloseRunner(sprint_service=sprint_service, uow=uow)
    publisher = RecordingPublisher()
    job = SprintCloseJob(closer=closer, reports=SprintReportPublisher(publisher))

    due_group_ids = await list_due_group_ids(uow=uow, clock=clock)
    assert due_group_ids == [1]

    first_closed_count = await job.run(
        due_group_ids=due_group_ids, correlation_id="scheduler-run-1"
    )
    assert first_closed_count == 1
    balances_after_first_run = dict(uow.groups.balances)
    commit_count_after_first_run = uow.commit_count
    notification_calls_after_first_run = len(publisher.calls)
    assert notification_calls_after_first_run > 0

    # Simulate the scheduler firing again for the same day (e.g. process
    # restart, overlapping trigger, or a retry). The window is still "due" by
    # date, but the period has already been closed.
    due_group_ids_again = await list_due_group_ids(uow=uow, clock=clock)
    assert due_group_ids_again == [1]

    second_closed_count = await job.run(
        due_group_ids=due_group_ids_again, correlation_id="scheduler-run-2"
    )

    assert second_closed_count == 0
    assert uow.groups.balances == balances_after_first_run
    assert uow.commit_count == commit_count_after_first_run
    assert len(publisher.calls) == notification_calls_after_first_run
    assert len(uow.sprints.sprint_runs) == 1
