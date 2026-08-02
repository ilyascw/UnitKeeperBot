from __future__ import annotations

from decimal import Decimal

import pytest
from db.enums import NotificationEventType, TaskLogStatus, Weekday

from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.application.tasks.service import TaskImportItem, TaskService
from unitkeeper_backend.domain.errors import (
    AuthorizationError,
    BusinessRuleViolation,
    NotFoundError,
    ValidationError,
)


@pytest.mark.asyncio
async def test_single_member_group_auto_completes_task() -> None:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "solo", "Solo", None, "en", False)
    group_service = GroupService(
        uow=uow,
        context_service=CurrentContextService(uow=uow),
        clock=FakeClock(utc_datetime(2026, 3, 16)),
    )
    await group_service.create_group(
        user_id=1,
        name="solo-group",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    task_service = TaskService(uow=uow, clock=FakeClock(utc_datetime(2026, 3, 16)))
    task = await task_service.create_task(
        group_id=1,
        title="Wash dishes",
        frequency_per_sprint=1,
        unit_cost=Decimal("5.00"),
    )

    log = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)

    assert log.status is TaskLogStatus.COMPLETED
    assert log.approver_user_id == 1


@pytest.mark.asyncio
async def test_multi_member_group_rejects_self_approval_and_frequency_overflow() -> None:
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
    task = await task_service.create_task(
        group_id=1,
        title="Vacuum",
        frequency_per_sprint=1,
        unit_cost=Decimal("4.00"),
    )

    pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
    assert pending.status is TaskLogStatus.PENDING
    approval_event = next(
        event
        for event in uow.notifications.events.values()
        if event.event_type is NotificationEventType.TASK_APPROVAL_REQUESTED
    )
    assert approval_event.event_type is NotificationEventType.TASK_APPROVAL_REQUESTED
    assert approval_event.recipient_user_id == 2
    assert approval_event.deep_link_path == f"/tasks/history?task_log_id={pending.id}"

    with pytest.raises(AuthorizationError):
        await task_service.approve(group_id=1, approver_user_id=1, log_id=pending.id)

    approved = await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)
    assert approved.status is TaskLogStatus.COMPLETED
    result_event = list(uow.notifications.events.values())[-1]
    assert result_event.event_type is NotificationEventType.TASK_APPROVED
    assert result_event.recipient_user_id == 1
    assert result_event.deep_link_path == f"/tasks/history?task_log_id={pending.id}"

    with pytest.raises(BusinessRuleViolation):
        await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)


@pytest.mark.asyncio
async def test_pending_hold_consumes_a_slot_and_blocks_over_marking() -> None:
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
    task = await task_service.create_task(
        group_id=1,
        title="Take out trash",
        frequency_per_sprint=1,
        unit_cost=Decimal("2.00"),
    )

    # A single unconfirmed (pending) completion already fills the only slot, so
    # nobody can mark it again until that hold is resolved.
    pending = await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)
    assert pending.status is TaskLogStatus.PENDING

    with pytest.raises(BusinessRuleViolation):
        await task_service.mark_done(group_id=1, performer_user_id=2, task_id=task.id)

    # The task list reflects the outstanding hold and zero remaining slots.
    listed = {t.id: t for t in await task_service.list_tasks(group_id=1)}
    assert listed[task.id].pending_in_sprint == 1
    assert listed[task.id].completed_in_sprint == 0
    assert listed[task.id].available_in_sprint == 0

    # Rejecting the hold frees the slot, so marking is possible again.
    await task_service.reject(
        group_id=1, approver_user_id=2, log_id=pending.id, rejection_reason="not done"
    )
    freed = await task_service.mark_done(group_id=1, performer_user_id=2, task_id=task.id)
    assert freed.status is TaskLogStatus.PENDING


async def _bootstrap_solo_group() -> tuple[InMemoryUnitOfWork, TaskService]:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "solo", "Solo", None, "en", False)
    group_service = GroupService(
        uow=uow,
        context_service=CurrentContextService(uow=uow),
        clock=FakeClock(utc_datetime(2026, 3, 16)),
    )
    await group_service.create_group(
        user_id=1,
        name="solo-group",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    return uow, TaskService(uow=uow, clock=FakeClock(utc_datetime(2026, 3, 16)))


@pytest.mark.asyncio
async def test_import_tasks_creates_all_when_payload_is_valid() -> None:
    uow, task_service = await _bootstrap_solo_group()

    created = await task_service.import_tasks(
        group_id=1,
        items=[
            TaskImportItem(title="Wash dishes ", frequency_per_sprint=2, unit_cost=Decimal("3.5")),
            TaskImportItem(title="Vacuum", frequency_per_sprint=1, unit_cost=Decimal("4")),
            TaskImportItem(title="Windows", frequency_per_sprint=0, unit_cost=Decimal("5")),
        ],
    )

    assert [t.title for t in created] == ["Wash dishes", "Vacuum", "Windows"]
    assert created[-1].frequency_per_sprint == 0
    assert all(t.id > 0 for t in created)
    assert len(uow.tasks.tasks) == 3
    assert uow.commit_count >= 1


@pytest.mark.asyncio
async def test_zero_frequency_task_is_not_available_for_current_sprint() -> None:
    _, task_service = await _bootstrap_solo_group()
    task = await task_service.create_task(
        group_id=1,
        title="Paused task",
        frequency_per_sprint=0,
        unit_cost=Decimal("5"),
    )

    assert task.remaining_in_sprint == 0
    assert task.available_in_sprint == 0
    with pytest.raises(BusinessRuleViolation):
        await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)


@pytest.mark.asyncio
async def test_import_tasks_rejects_payload_with_invalid_rows_and_creates_nothing() -> None:
    uow, task_service = await _bootstrap_solo_group()

    with pytest.raises(ValidationError) as exc_info:
        await task_service.import_tasks(
            group_id=1,
            items=[
                TaskImportItem(title="Good", frequency_per_sprint=1, unit_cost=Decimal("1")),
                TaskImportItem(title="  ", frequency_per_sprint=0, unit_cost=Decimal("-1")),
                TaskImportItem(title="Bad freq", frequency_per_sprint=-3, unit_cost=Decimal("0")),
            ],
        )

    details = exc_info.value.details
    assert isinstance(details, dict)
    errors = details["errors"]
    indexes = {entry["index"] for entry in errors}
    assert indexes == {1, 2}
    fields_at_index_1 = {entry["field"] for entry in errors if entry["index"] == 1}
    assert fields_at_index_1 == {"title", "unit_cost"}
    assert uow.tasks.tasks == {}


@pytest.mark.asyncio
async def test_import_tasks_rejects_empty_payload() -> None:
    _, task_service = await _bootstrap_solo_group()

    with pytest.raises(ValidationError):
        await task_service.import_tasks(group_id=1, items=[])


@pytest.mark.asyncio
async def test_adjust_frequency_increases_and_decreases_within_bounds() -> None:
    _, task_service = await _bootstrap_solo_group()
    task = await task_service.create_task(
        group_id=1, title="Run", frequency_per_sprint=2, unit_cost=Decimal("1")
    )

    increased = await task_service.adjust_frequency(group_id=1, task_id=task.id, delta=3)
    assert increased.frequency_per_sprint == 5

    decreased = await task_service.adjust_frequency(group_id=1, task_id=task.id, delta=-5)
    assert decreased.frequency_per_sprint == 0

    with pytest.raises(ValidationError):
        await task_service.adjust_frequency(group_id=1, task_id=task.id, delta=-1)

    with pytest.raises(ValidationError):
        await task_service.adjust_frequency(group_id=1, task_id=task.id, delta=0)


@pytest.mark.asyncio
async def test_adjust_frequency_rejects_soft_deleted_task() -> None:
    _, task_service = await _bootstrap_solo_group()
    task = await task_service.create_task(
        group_id=1, title="Run", frequency_per_sprint=2, unit_cost=Decimal("1")
    )
    await task_service.delete_task(group_id=1, task_id=task.id)

    with pytest.raises(BusinessRuleViolation):
        await task_service.adjust_frequency(group_id=1, task_id=task.id, delta=1)


@pytest.mark.asyncio
async def test_task_log_queries_enforce_visibility_and_return_enriched_filtered_pages() -> None:
    uow = InMemoryUnitOfWork()
    for user_id in (1, 2, 3):
        uow.users.users[user_id] = UserProfile(
            user_id, f"user{user_id}", f"User {user_id}", None, "en", False
        )
    clock = FakeClock(utc_datetime(2026, 3, 16))
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
    first_task = await task_service.create_task(
        group_id=1, title="Dishes", frequency_per_sprint=3, unit_cost=Decimal("2")
    )
    second_task = await task_service.create_task(
        group_id=1, title="Vacuum", frequency_per_sprint=3, unit_cost=Decimal("4")
    )
    own_pending = await task_service.mark_done(
        group_id=1, performer_user_id=1, task_id=first_task.id
    )
    other_pending = await task_service.mark_done(
        group_id=1, performer_user_id=2, task_id=second_task.id
    )
    rejected = await task_service.reject(
        group_id=1,
        approver_user_id=2,
        log_id=own_pending.id,
        rejection_reason="Needs a photo",
    )

    pending_for_user_1 = await task_service.list_pending_approvals(
        group_id=1, user_id=1, limit=50, offset=0
    )
    assert [item.id for item in pending_for_user_1.items] == [other_pending.id]
    assert pending_for_user_1.items[0].task_title == "Vacuum"
    assert pending_for_user_1.items[0].performer.id == 2

    mine = await task_service.list_my_task_logs(
        group_id=1,
        user_id=1,
        task_id=first_task.id,
        statuses=[TaskLogStatus.REJECTED],
        limit=1,
        offset=0,
    )
    assert mine.total == 1
    assert mine.has_more is False
    assert mine.items[0].id == rejected.id
    assert mine.items[0].rejection_reason == "Needs a photo"
    assert mine.items[0].approver is not None
    assert mine.items[0].approver.id == 2

    history = await task_service.list_group_task_logs(
        group_id=1,
        user_id=2,
        performer_user_id=None,
        task_id=None,
        statuses=None,
        limit=1,
        offset=1,
    )
    assert history.total == 2
    assert len(history.items) == 1

    detail = await task_service.get_task_log_view(group_id=1, user_id=2, log_id=rejected.id)
    assert detail.task_title == "Dishes"

    with pytest.raises(AuthorizationError):
        await task_service.list_group_task_logs(
            group_id=1,
            user_id=3,
            performer_user_id=None,
            task_id=None,
            statuses=None,
            limit=50,
            offset=0,
        )
    with pytest.raises(NotFoundError):
        await task_service.get_task_log_view(group_id=1, user_id=2, log_id=999)
