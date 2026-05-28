from __future__ import annotations

from decimal import Decimal

import pytest

from db.enums import TaskLogStatus, Weekday
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.application.tasks.service import TaskImportItem, TaskService
from unitkeeper_backend.domain.errors import AuthorizationError, BusinessRuleViolation, ValidationError
from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime


@pytest.mark.asyncio
async def test_single_member_group_auto_completes_task() -> None:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "solo", "Solo", None, "en", False)
    group_service = GroupService(uow=uow, context_service=CurrentContextService(uow=uow), clock=FakeClock(utc_datetime(2026, 3, 16)))
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
        uow.users.users[user_id] = UserProfile(user_id, f"user{user_id}", f"User {user_id}", None, "en", False)
    group_service = GroupService(uow=uow, context_service=CurrentContextService(uow=uow), clock=FakeClock(utc_datetime(2026, 3, 16)))
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

    with pytest.raises(AuthorizationError):
        await task_service.approve(group_id=1, approver_user_id=1, log_id=pending.id)

    approved = await task_service.approve(group_id=1, approver_user_id=2, log_id=pending.id)
    assert approved.status is TaskLogStatus.COMPLETED

    with pytest.raises(BusinessRuleViolation):
        await task_service.mark_done(group_id=1, performer_user_id=1, task_id=task.id)


async def _bootstrap_solo_group() -> tuple[InMemoryUnitOfWork, TaskService]:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "solo", "Solo", None, "en", False)
    group_service = GroupService(uow=uow, context_service=CurrentContextService(uow=uow), clock=FakeClock(utc_datetime(2026, 3, 16)))
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
        ],
    )

    assert [t.title for t in created] == ["Wash dishes", "Vacuum"]
    assert all(t.id > 0 for t in created)
    assert len(uow.tasks.tasks) == 2
    assert uow.commit_count >= 1


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
    assert fields_at_index_1 == {"title", "frequency_per_sprint", "unit_cost"}
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

    decreased = await task_service.adjust_frequency(group_id=1, task_id=task.id, delta=-4)
    assert decreased.frequency_per_sprint == 1

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
