from __future__ import annotations

from decimal import Decimal

import pytest

from db.enums import Weekday
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.domain.errors import AuthorizationError, ValidationError
from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime


def _build_service(uow: InMemoryUnitOfWork) -> GroupService:
    return GroupService(
        uow=uow,
        context_service=CurrentContextService(uow=uow),
        clock=FakeClock(utc_datetime(2026, 3, 16)),
    )


@pytest.mark.asyncio
async def test_create_group_initializes_owner_context() -> None:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "alice", "Alice", None, "en", False)
    service = GroupService(uow=uow, context_service=CurrentContextService(uow=uow), clock=FakeClock(utc_datetime(2026, 3, 16)))

    context = await service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=14,
        timezone="UTC",
    )

    assert context.group is not None
    assert context.group.owner_user_id == 1
    assert context.membership is not None
    assert context.membership.weight_percent == Decimal("100.00")
    assert uow.groups.balances[(context.group.id, 1)] == Decimal("0.00")


@pytest.mark.asyncio
async def test_join_and_leave_rebalance_weights_and_handover_owner() -> None:
    uow = InMemoryUnitOfWork()
    uow.users.users[1] = UserProfile(1, "owner", "Owner", None, "en", False)
    uow.users.users[2] = UserProfile(2, "member", "Member", None, "en", False)
    uow.users.users[3] = UserProfile(3, "third", "Third", None, "en", False)
    service = GroupService(uow=uow, context_service=CurrentContextService(uow=uow), clock=FakeClock(utc_datetime(2026, 3, 16)))

    await service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=14,
        timezone="UTC",
    )
    await service.join_group(user_id=2, group_name="team", join_secret="secret")
    await service.join_group(user_id=3, group_name="team", join_secret="secret")

    memberships = await uow.groups.list_active_memberships(1)
    assert {membership.user_id: membership.weight_percent for membership in memberships} == {
        1: Decimal("33.33"),
        2: Decimal("33.33"),
        3: Decimal("33.34"),
    }

    await service.leave_group(user_id=1, left_at=utc_datetime(2026, 3, 16))
    group = await uow.groups.get_by_id(1)
    remaining = await uow.groups.list_active_memberships(1)

    assert group is not None
    assert group.owner_user_id == 2
    assert {membership.user_id: membership.weight_percent for membership in remaining} == {
        2: Decimal("50.00"),
        3: Decimal("50.00"),
    }


async def _seed_two_member_group(uow: InMemoryUnitOfWork) -> GroupService:
    uow.users.users[1] = UserProfile(1, "owner", "Owner", None, "en", False)
    uow.users.users[2] = UserProfile(2, "member", "Member", None, "en", False)
    service = _build_service(uow)
    await service.create_group(
        user_id=1,
        name="team",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=14,
        timezone="UTC",
    )
    await service.join_group(user_id=2, group_name="team", join_secret="secret")
    return service


@pytest.mark.asyncio
async def test_get_current_group_card_returns_sprint_window_and_members() -> None:
    uow = InMemoryUnitOfWork()
    service = await _seed_two_member_group(uow)
    uow.groups.balances[(1, 1)] = Decimal("12.50")
    uow.groups.balances[(1, 2)] = Decimal("-3.00")

    card = await service.get_current_group_card(user_id=1)

    assert card.owner_user_id == 1
    assert card.join_secret == "secret"
    assert card.sprint_period_start.weekday() == 0
    assert (card.sprint_period_end - card.sprint_period_start).days == 13
    assert card.sprint_ends_at.hour == 0
    assert [m.user_id for m in card.members] == [1, 2]
    assert card.members[0].is_owner is True
    assert card.members[0].balance == Decimal("12.50")
    assert card.members[1].balance == Decimal("-3.00")

    card_for_member = await service.get_current_group_card(user_id=2)
    assert card_for_member.join_secret is None


@pytest.mark.asyncio
async def test_update_settings_requires_owner_and_validates() -> None:
    uow = InMemoryUnitOfWork()
    service = await _seed_two_member_group(uow)

    with pytest.raises(AuthorizationError):
        await service.update_current_group_settings(
            user_id=2,
            join_secret="newsecret",
            sprint_start_weekday=None,
            sprint_duration_days=None,
        )

    with pytest.raises(ValidationError):
        await service.update_current_group_settings(
            user_id=1,
            join_secret=None,
            sprint_start_weekday=None,
            sprint_duration_days=10,
        )

    updated = await service.update_current_group_settings(
        user_id=1,
        join_secret="rotated",
        sprint_start_weekday=Weekday.WEDNESDAY,
        sprint_duration_days=7,
    )
    assert updated.join_secret == "rotated"
    assert updated.sprint_start_weekday is Weekday.WEDNESDAY
    assert updated.sprint_duration_days == 7


@pytest.mark.asyncio
async def test_update_weights_validates_sum_and_membership() -> None:
    uow = InMemoryUnitOfWork()
    service = await _seed_two_member_group(uow)

    with pytest.raises(AuthorizationError):
        await service.update_current_group_weights(
            user_id=2,
            weights_by_user_id={1: Decimal("60"), 2: Decimal("40")},
        )

    with pytest.raises(ValidationError):
        await service.update_current_group_weights(
            user_id=1,
            weights_by_user_id={1: Decimal("60"), 2: Decimal("30")},
        )

    with pytest.raises(ValidationError):
        await service.update_current_group_weights(
            user_id=1,
            weights_by_user_id={1: Decimal("100")},
        )

    with pytest.raises(ValidationError):
        await service.update_current_group_weights(
            user_id=1,
            weights_by_user_id={1: Decimal("110"), 2: Decimal("-10")},
        )

    members = await service.update_current_group_weights(
        user_id=1,
        weights_by_user_id={1: Decimal("70"), 2: Decimal("30")},
    )
    by_id = {m.user_id: m.weight_percent for m in members}
    assert by_id == {1: Decimal("70.00"), 2: Decimal("30.00")}
