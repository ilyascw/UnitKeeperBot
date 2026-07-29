from __future__ import annotations

from decimal import Decimal

import pytest
from db.enums import Weekday

from tests.support.fakes import FakeClock, InMemoryUnitOfWork, utc_datetime
from unitkeeper_backend.application.balances.service import BalanceService
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.groups.service import GroupService
from unitkeeper_backend.application.models import UserProfile
from unitkeeper_backend.domain.errors import BusinessRuleViolation, ValidationError


async def _seed_group() -> tuple[InMemoryUnitOfWork, BalanceService]:
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
        name="primary",
        join_secret="secret",
        sprint_start_weekday=Weekday.MONDAY,
        sprint_duration_days=7,
        timezone="UTC",
    )
    await group_service.join_group(user_id=2, group_name="primary", join_secret="secret")
    return uow, BalanceService(uow=uow)


@pytest.mark.asyncio
async def test_transfer_updates_balances_and_writes_double_ledger_entries() -> None:
    uow, service = await _seed_group()
    uow.groups.balances[(1, 1)] = Decimal("12.50")

    transfer = await service.transfer(sender_user_id=1, recipient_user_id=2, amount=Decimal("3.25"))

    assert transfer.sender_balance == Decimal("9.25")
    assert transfer.recipient_balance == Decimal("3.25")
    assert uow.commit_count == 3
    assert [
        (item.user_id, item.amount_delta, item.counterparty_user_id)
        for item in uow.sprints.balance_transactions
    ] == [
        (1, Decimal("-3.25"), 2),
        (2, Decimal("3.25"), 1),
    ]


@pytest.mark.asyncio
async def test_transfer_rejects_insufficient_balance_without_ledger_writes() -> None:
    uow, service = await _seed_group()
    uow.groups.balances[(1, 1)] = Decimal("2.00")

    with pytest.raises(BusinessRuleViolation, match="Insufficient"):
        await service.transfer(sender_user_id=1, recipient_user_id=2, amount=Decimal("2.01"))

    assert uow.groups.balances[(1, 1)] == Decimal("2.00")
    assert not uow.sprints.balance_transactions


@pytest.mark.asyncio
async def test_transfer_rejects_self_transfer_and_member_from_another_group() -> None:
    uow, service = await _seed_group()

    with pytest.raises(ValidationError, match="yourself"):
        await service.transfer(sender_user_id=1, recipient_user_id=1, amount=Decimal("1.00"))
    with pytest.raises(BusinessRuleViolation, match="active member"):
        await service.transfer(sender_user_id=1, recipient_user_id=3, amount=Decimal("1.00"))


@pytest.mark.asyncio
async def test_balance_read_candidates_and_transaction_history_use_current_group() -> None:
    uow, service = await _seed_group()
    uow.groups.balances[(1, 1)] = Decimal("5.00")
    uow.groups.balances[(1, 2)] = Decimal("1.00")
    await service.transfer(sender_user_id=1, recipient_user_id=2, amount=Decimal("2.00"))

    balance = await service.get_my_balance(user_id=1)
    candidates = await service.list_transfer_candidates(user_id=1)
    history = await service.list_my_transactions(user_id=1, limit=10, offset=0)

    assert balance.current_balance == Decimal("3.00")
    assert [(item.user.id, item.current_balance) for item in candidates] == [(2, Decimal("3.00"))]
    assert history.total == 1
    assert history.items[0].amount_delta == Decimal("-2.00")
