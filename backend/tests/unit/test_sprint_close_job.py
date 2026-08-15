from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from db.enums import TaskLogStatus, Weekday

from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.jobs.sprint_close import (
    SprintCloseRunner,
    list_due_sprint_windows,
)
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.application.tasks.service import TaskService
from unitkeeper_backend.domain.errors import BusinessRuleViolation

MOSCOW = ZoneInfo("Europe/Moscow")


def moscow_datetime(year: int, month: int, day: int, hour: int = 12) -> datetime:
    return datetime(year, month, day, hour, tzinfo=MOSCOW)


async def _build_group(
    uow: InMemoryUnitOfWork,
    *,
    clock: FakeClock,
    sprint_duration_days: int = 7,
    group_timezone: str = "UTC",
    with_completion: bool = True,
) -> None:
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
        sprint_duration_days=sprint_duration_days,
        timezone=group_timezone,
    )
    await group_service.join_group(user_id=2, group_name="team", join_secret="secret")
    task_service = TaskService(uow=uow, clock=clock)
    task = await task_service.create_task(
        group_id=1, title="Laundry", frequency_per_sprint=2, unit_cost=Decimal("3.00")
    )
    if with_completion:
        pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
        await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)


async def _complete_task_at(
    uow: InMemoryUnitOfWork, *, at: datetime, performer_user_id: int = 1
) -> None:
    clock = FakeClock(at)
    task_service = TaskService(uow=uow, clock=clock)
    pending = await task_service.mark_done(
        group_id=1, performer_user_id=performer_user_id, task_id=1
    )
    await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)


@pytest.mark.asyncio
async def test_moscow_group_is_not_due_during_its_final_local_day() -> None:
    """The bug this change fixes: 00:05 UTC is 03:05 on the last local day."""
    uow = InMemoryUnitOfWork()
    await _build_group(
        uow, clock=FakeClock(moscow_datetime(2026, 8, 10)), group_timezone="Europe/Moscow"
    )

    still_running = FakeClock(datetime(2026, 8, 16, 0, 5, tzinfo=timezone.utc))
    assert await list_due_sprint_windows(uow=uow, clock=still_running) == []

    # 2026-08-16T20:55Z is 23:55 Moscow — still the final day.
    almost = FakeClock(datetime(2026, 8, 16, 20, 55, tzinfo=timezone.utc))
    assert await list_due_sprint_windows(uow=uow, clock=almost) == []


@pytest.mark.asyncio
async def test_moscow_group_becomes_due_at_its_own_local_boundary() -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(
        uow, clock=FakeClock(moscow_datetime(2026, 8, 10)), group_timezone="Europe/Moscow"
    )

    # 2026-08-16T21:00Z == 2026-08-17T00:00+03:00.
    boundary = FakeClock(datetime(2026, 8, 16, 21, tzinfo=timezone.utc))
    due = await list_due_sprint_windows(uow=uow, clock=boundary)
    assert [(item.group_id, item.period_start, item.period_end) for item in due] == [
        (1, date(2026, 8, 10), date(2026, 8, 16))
    ]


@pytest.mark.asyncio
async def test_completion_late_on_the_final_local_day_is_counted() -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(
        uow,
        clock=FakeClock(moscow_datetime(2026, 8, 10)),
        group_timezone="Europe/Moscow",
        with_completion=False,
    )
    await _complete_task_at(uow, at=moscow_datetime(2026, 8, 16, 23).replace(minute=30))

    clock = FakeClock(datetime(2026, 8, 16, 21, tzinfo=timezone.utc))
    runner = SprintCloseRunner(sprint_service=SprintService(uow=uow, clock=clock), uow=uow)
    closed = await runner.close_due_sprint(
        group_id=1,
        period_start=date(2026, 8, 10),
        period_end=date(2026, 8, 16),
        correlation_id="close-1",
    )

    assert closed is not None
    assert closed.completed_units == "3.00"


@pytest.mark.asyncio
async def test_two_windows_missed_during_downtime_are_settled_oldest_first() -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(
        uow,
        clock=FakeClock(moscow_datetime(2026, 8, 3)),
        group_timezone="Europe/Moscow",
        with_completion=False,
    )
    # One completion in each of the two windows that will be missed.
    await _complete_task_at(uow, at=moscow_datetime(2026, 8, 5))
    await _complete_task_at(uow, at=moscow_datetime(2026, 8, 12))

    # The scheduler comes back mid-window three, after 08-03..08-09 and
    # 08-10..08-16 have both ended locally.
    clock = FakeClock(moscow_datetime(2026, 8, 19))
    due = await list_due_sprint_windows(uow=uow, clock=clock)
    assert [(item.period_start, item.period_end) for item in due] == [
        (date(2026, 8, 3), date(2026, 8, 9)),
        (date(2026, 8, 10), date(2026, 8, 16)),
    ]

    runner = SprintCloseRunner(sprint_service=SprintService(uow=uow, clock=clock), uow=uow)
    closed = [
        await runner.close_due_sprint(
            group_id=item.group_id,
            period_start=item.period_start,
            period_end=item.period_end,
            correlation_id="catch-up",
        )
        for item in due
    ]

    assert [item.period for item in closed if item is not None] == [
        "2026-08-03..2026-08-09",
        "2026-08-10..2026-08-16",
    ]
    # Each settlement counts only the completion inside its own bounds.
    assert [item.completed_units for item in closed if item is not None] == ["3.00", "3.00"]


@pytest.mark.asyncio
async def test_backward_walk_is_capped_and_says_so(caplog: pytest.LogCaptureFixture) -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(uow, clock=FakeClock(utc_datetime(2026, 1, 5)))

    # Nothing was ever closed and ~24 windows have elapsed; the walk must stop
    # at the cap rather than replaying the group's whole history.
    clock = FakeClock(utc_datetime(2026, 6, 22))
    with caplog.at_level("WARNING"):
        due = await list_due_sprint_windows(uow=uow, clock=clock, lookback_windows=3)

    assert len(due) == 3
    assert [item.period_end for item in due] == [
        date(2026, 6, 7),
        date(2026, 6, 14),
        date(2026, 6, 21),
    ]
    assert "sprint_close.lookback_cap_reached" in caplog.text


@pytest.mark.asyncio
async def test_repeated_passes_settle_nothing_once_the_window_is_closed() -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(uow, clock=FakeClock(utc_datetime(2026, 3, 16)))

    clock = FakeClock(utc_datetime(2026, 3, 23))
    due = await list_due_sprint_windows(uow=uow, clock=clock)
    assert len(due) == 1

    runner = SprintCloseRunner(sprint_service=SprintService(uow=uow, clock=clock), uow=uow)
    assert (
        await runner.close_due_sprint(
            group_id=1,
            period_start=due[0].period_start,
            period_end=due[0].period_end,
            correlation_id="close-1",
        )
        is not None
    )

    assert await list_due_sprint_windows(uow=uow, clock=clock) == []
    # And the explicit-period path is still guarded, not just discovery.
    assert (
        await runner.close_due_sprint(
            group_id=1,
            period_start=due[0].period_start,
            period_end=due[0].period_end,
            correlation_id="close-2",
        )
        is None
    )


@pytest.mark.asyncio
async def test_manual_close_of_a_running_window_is_rejected_and_changes_nothing() -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(uow, clock=FakeClock(utc_datetime(2026, 3, 16)))

    clock = FakeClock(utc_datetime(2026, 3, 18))  # mid-window
    sprint_service = SprintService(uow=uow, clock=clock)
    balances_before = dict(uow.groups.balances)
    logs_before = {log_id: log.status for log_id, log in uow.tasks.logs.items()}

    with pytest.raises(BusinessRuleViolation):
        await sprint_service.close_current_sprint(group_id=1)

    assert uow.sprints.sprint_runs == {}
    assert uow.groups.balances == balances_before
    assert {log_id: log.status for log_id, log in uow.tasks.logs.items()} == logs_before


@pytest.mark.asyncio
async def test_pending_mark_from_a_later_window_survives_a_catch_up_close() -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(
        uow,
        clock=FakeClock(moscow_datetime(2026, 8, 3)),
        group_timezone="Europe/Moscow",
        with_completion=False,
    )
    stale_clock = FakeClock(moscow_datetime(2026, 8, 5))
    stale = await TaskService(uow=uow, clock=stale_clock).mark_done(
        group_id=1, performer_user_id=1, task_id=1
    )
    later_clock = FakeClock(moscow_datetime(2026, 8, 12))
    later_service = TaskService(uow=uow, clock=later_clock)
    later = await later_service.mark_done(group_id=1, performer_user_id=1, task_id=1)

    # Settle only the first window, while the second one is still running.
    clock = FakeClock(moscow_datetime(2026, 8, 13))
    await SprintService(uow=uow, clock=clock).close_current_sprint(
        group_id=1, period_start=date(2026, 8, 3), period_end=date(2026, 8, 9)
    )

    assert (await uow.tasks.get_task_log(log_id=stale.id)).status is TaskLogStatus.REJECTED
    surviving = await uow.tasks.get_task_log(log_id=later.id)
    assert surviving.status is TaskLogStatus.PENDING
    approved = await later_service.approve(group_id=1, approver_user_id=2, log_id=later.id)
    assert approved.status is TaskLogStatus.COMPLETED


@pytest.mark.asyncio
async def test_unresolvable_timezone_falls_back_to_utc_without_blocking_other_groups(
    caplog: pytest.LogCaptureFixture,
) -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(uow, clock=FakeClock(utc_datetime(2026, 3, 16)))
    # A second group sharing the first one's members isn't representable here,
    # so clone the stored row directly — the point is a corrupt timezone value.
    uow.groups.groups[2] = replace(uow.groups.groups[1], id=2, name="broken", timezone="Mars/Base")
    for membership_id, membership in list(uow.groups.memberships.items()):
        uow.groups.memberships[membership_id + 100] = replace(
            membership, id=membership_id + 100, group_id=2
        )

    clock = FakeClock(utc_datetime(2026, 3, 23))
    with caplog.at_level("WARNING"):
        due = await list_due_sprint_windows(uow=uow, clock=clock)

    assert "group.timezone_unresolvable" in caplog.text
    assert "group_id=2" in caplog.text
    # The broken group is evaluated in UTC and both groups are still processed.
    assert sorted(item.group_id for item in due) == [1, 2]
    assert all(item.period_end == date(2026, 3, 22) for item in due)


@pytest.mark.asyncio
@pytest.mark.parametrize("sprint_duration_days", [7, 14, 21, 28])
async def test_due_only_after_the_window_ends_for_any_sprint_length(
    sprint_duration_days: int,
) -> None:
    uow = InMemoryUnitOfWork()
    start = utc_datetime(2026, 3, 16)
    await _build_group(uow, clock=FakeClock(start), sprint_duration_days=sprint_duration_days)

    last_day = start + timedelta(days=sprint_duration_days - 1)
    assert await list_due_sprint_windows(uow=uow, clock=FakeClock(last_day)) == []

    after_end = start + timedelta(days=sprint_duration_days)
    due = await list_due_sprint_windows(uow=uow, clock=FakeClock(after_end))
    assert [(item.period_start, item.period_end) for item in due] == [
        (start.date(), last_day.date())
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("sprint_duration_days", [7, 14, 21, 28])
async def test_sprint_close_runner_closes_multi_week_sprint_and_skips_duplicate_close(
    sprint_duration_days: int,
) -> None:
    uow = InMemoryUnitOfWork()
    creation_clock = FakeClock(utc_datetime(2026, 3, 16))
    await _build_group(uow, clock=creation_clock, sprint_duration_days=sprint_duration_days)

    last_day = utc_datetime(2026, 3, 16) + timedelta(days=sprint_duration_days - 1)
    clock = FakeClock(last_day + timedelta(days=1))
    runner = SprintCloseRunner(sprint_service=SprintService(uow=uow, clock=clock), uow=uow)

    closed = await runner.close_due_sprint(
        group_id=1,
        period_start=date(2026, 3, 16),
        period_end=last_day.date(),
        correlation_id="close-1",
    )
    assert closed is not None
    assert closed.group_id == 1
    assert closed.period == f"2026-03-16..{last_day.date().isoformat()}"

    repeated = await runner.close_due_sprint(
        group_id=1,
        period_start=date(2026, 3, 16),
        period_end=last_day.date(),
        correlation_id="close-2",
    )
    assert repeated is None


@pytest.mark.asyncio
async def test_sprint_close_runner_closes_once_and_skips_duplicate_close(
    caplog: pytest.LogCaptureFixture,
) -> None:
    uow = InMemoryUnitOfWork()
    await _build_group(uow, clock=FakeClock(utc_datetime(2026, 3, 16)))
    clock = FakeClock(utc_datetime(2026, 3, 23))
    runner = SprintCloseRunner(sprint_service=SprintService(uow=uow, clock=clock), uow=uow)

    with caplog.at_level("INFO"):
        closed = await runner.close_due_sprint(
            group_id=1,
            period_start=date(2026, 3, 16),
            period_end=date(2026, 3, 22),
            correlation_id="close-1",
        )
    assert closed is not None
    assert closed.group_id == 1
    assert len(closed.reports) == 2
    assert "sprint_close.closed" in caplog.text

    caplog.clear()
    with caplog.at_level("INFO"):
        repeated = await runner.close_due_sprint(
            group_id=1,
            period_start=date(2026, 3, 16),
            period_end=date(2026, 3, 22),
            correlation_id="close-2",
        )
    assert repeated is None
    assert "sprint_close.duplicate_skipped" in caplog.text


@pytest.mark.asyncio
async def test_sprint_close_runner_skips_unknown_group() -> None:
    uow = InMemoryUnitOfWork()
    clock = FakeClock(utc_datetime(2026, 3, 23))
    runner = SprintCloseRunner(sprint_service=SprintService(uow=uow, clock=clock), uow=uow)

    result = await runner.close_due_sprint(
        group_id=999,
        period_start=date(2026, 3, 16),
        period_end=date(2026, 3, 22),
        correlation_id="close-missing",
    )
    assert result is None
