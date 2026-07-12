from __future__ import annotations

from decimal import Decimal

from db.enums import BalanceTransactionType
from unitkeeper_backend.application.models import (
    BalanceInfo,
    BalanceTransactionPage,
    BalanceTransferInfo,
    TransferCandidateInfo,
)
from unitkeeper_backend.application.ports import UnitOfWork
from unitkeeper_backend.domain.errors import BusinessRuleViolation, NotFoundError, ValidationError


class BalanceService:
    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    async def get_my_balance(self, *, user_id: int) -> BalanceInfo:
        group_id = await self._require_active_group(user_id=user_id)
        balance = await self._uow.groups.get_balance(group_id=group_id, user_id=user_id)
        return BalanceInfo(group_id=group_id, user_id=user_id, current_balance=balance)

    async def list_transfer_candidates(self, *, user_id: int) -> list[TransferCandidateInfo]:
        group_id = await self._require_active_group(user_id=user_id)
        memberships = await self._uow.groups.list_active_memberships(group_id)
        candidate_ids = sorted(item.user_id for item in memberships if item.user_id != user_id)
        users = {item.id: item for item in await self._uow.users.list_by_ids(candidate_ids)}
        balances = await self._uow.groups.list_member_balances(group_id)
        return [
            TransferCandidateInfo(user=users[candidate_id], current_balance=balances.get(candidate_id, Decimal("0.00")))
            for candidate_id in candidate_ids
            if candidate_id in users
        ]

    async def transfer(
        self,
        *,
        sender_user_id: int,
        recipient_user_id: int,
        amount: Decimal,
    ) -> BalanceTransferInfo:
        if amount <= Decimal("0"):
            raise ValidationError("Transfer amount must be greater than zero")
        if sender_user_id == recipient_user_id:
            raise ValidationError("Cannot transfer units to yourself")

        group_id = await self._require_active_group(user_id=sender_user_id)
        recipient_membership = await self._uow.groups.get_active_membership_in_group(
            group_id=group_id,
            user_id=recipient_user_id,
        )
        if recipient_membership is None:
            raise BusinessRuleViolation("Recipient must be an active member of the current group")

        await self._uow.groups.ensure_balance(group_id=group_id, user_id=sender_user_id)
        await self._uow.groups.ensure_balance(group_id=group_id, user_id=recipient_user_id)
        sender_balance, recipient_balance = await self._uow.groups.transfer_balance(
            group_id=group_id,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            amount=amount,
        )
        await self._uow.sprints.add_balance_transaction(
            group_id=group_id,
            user_id=sender_user_id,
            transaction_type=BalanceTransactionType.TRANSFER,
            amount_delta=-amount,
            counterparty_user_id=recipient_user_id,
            description=f"Transfer to user {recipient_user_id}",
        )
        await self._uow.sprints.add_balance_transaction(
            group_id=group_id,
            user_id=recipient_user_id,
            transaction_type=BalanceTransactionType.TRANSFER,
            amount_delta=amount,
            counterparty_user_id=sender_user_id,
            description=f"Transfer from user {sender_user_id}",
        )
        await self._uow.commit()
        return BalanceTransferInfo(
            group_id=group_id,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            amount=amount,
            sender_balance=sender_balance,
            recipient_balance=recipient_balance,
        )

    async def list_my_transactions(
        self,
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> BalanceTransactionPage:
        group_id = await self._require_active_group(user_id=user_id)
        items, total = await self._uow.sprints.list_balance_transactions(
            group_id=group_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
        return BalanceTransactionPage(items=items, total=total, limit=limit, offset=offset)

    async def _require_active_group(self, *, user_id: int) -> int:
        membership = await self._uow.groups.get_active_membership(user_id)
        if membership is None:
            raise NotFoundError("User has no active group")
        return membership.group_id
