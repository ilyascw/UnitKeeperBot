from __future__ import annotations

from decimal import Decimal

import pytest

from db.enums import TaskLogStatus, Weekday
from unitkeeper_backend.application.bot.service import BotService
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.models import TelegramIdentity, UserProfile
from unitkeeper_backend.application.tasks.service import TaskService
from unitkeeper_backend.domain.errors import AuthorizationError, NotFoundError
from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime


def _build(uow: InMemoryUnitOfWork) -> BotService:
    context_service = CurrentContextService(uow=uow)
    task_service = TaskService(uow=uow, clock=FakeClock(utc_datetime(2026, 3, 16)))
    return BotService(uow=uow, context_service=context_service, task_service=task_service)


@pytest.mark.asyncio
async def test_ensure_user_upserts_profile_from_telegram_identity() -> None:
    uow = InMemoryUnitOfWork()
    bot = _build(uow)

    user = await bot.ensure_user(
        TelegramIdentity(
            user_id=42,
            username="ivan",
            first_name="Ivan",
            last_name=None,
            language_code="ru",
            is_bot=False,
        )
    )

    assert user.id == 42
    assert uow.users.users[42].username == "ivan"
    assert uow.commit_count == 1


@pytest.mark.asyncio
async def test_get_context_returns_empty_group_for_brand_new_user() -> None:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "solo", "Solo", None, "en", False)
    bot = _build(uow)

    context = await bot.get_context(1)

    assert context.user.id == 1
    assert context.group is None


@pytest.mark.asyncio
async def test_approve_via_bot_promotes_pending_log_to_completed() -> None:
    uow = InMemoryUnitOfWork()
    for uid in (1, 2):
        uow.users.users[uid] = UserProfile(uid, f"u{uid}", f"U{uid}", None, "en", False)
    context_service = CurrentContextService(uow=uow)
    group_service = GroupService(uow=uow, context_service=context_service, clock=FakeClock(utc_datetime(2026, 3, 16)))
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
    bot = BotService(uow=uow, context_service=context_service, task_service=task_service)

    approved = await bot.approve(telegram_user_id=2, log_id=pending.id)

    assert approved.status is TaskLogStatus.COMPLETED
    assert approved.approver_user_id == 2


@pytest.mark.asyncio
async def test_reject_via_bot_marks_log_rejected_with_reason() -> None:
    uow = InMemoryUnitOfWork()
    for uid in (1, 2):
        uow.users.users[uid] = UserProfile(uid, f"u{uid}", f"U{uid}", None, "en", False)
    context_service = CurrentContextService(uow=uow)
    group_service = GroupService(uow=uow, context_service=context_service, clock=FakeClock(utc_datetime(2026, 3, 16)))
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
    bot = BotService(uow=uow, context_service=context_service, task_service=task_service)

    rejected = await bot.reject(telegram_user_id=2, log_id=pending.id, reason="not done")

    assert rejected.status is TaskLogStatus.REJECTED
    assert rejected.rejection_reason == "not done"


@pytest.mark.asyncio
async def test_approve_forbidden_for_user_without_active_group() -> None:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "solo", "Solo", None, "en", False)
    bot = _build(uow)

    with pytest.raises(NotFoundError):
        await bot.approve(telegram_user_id=1, log_id=999)


@pytest.mark.asyncio
async def test_performer_cannot_self_approve_via_bot_in_multi_member_group() -> None:
    uow = InMemoryUnitOfWork()
    for uid in (1, 2):
        uow.users.users[uid] = UserProfile(uid, f"u{uid}", f"U{uid}", None, "en", False)
    context_service = CurrentContextService(uow=uow)
    group_service = GroupService(uow=uow, context_service=context_service, clock=FakeClock(utc_datetime(2026, 3, 16)))
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
    bot = BotService(uow=uow, context_service=context_service, task_service=task_service)

    with pytest.raises(AuthorizationError):
        await bot.approve(telegram_user_id=1, log_id=pending.id)
