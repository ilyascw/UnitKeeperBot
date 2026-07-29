from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal

from db.enums import Weekday
from db.models import Balance, Group, GroupMembership, GroupMemberWeight
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unitkeeper_backend.application.models import GroupInfo, MembershipInfo
from unitkeeper_backend.domain.errors import BusinessRuleViolation, NotFoundError
from unitkeeper_backend.infrastructure.repositories.mappers import map_group, map_membership


class SqlAlchemyGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, group_id: int) -> GroupInfo | None:
        model = await self._fetch_group(group_id=group_id)
        return map_group(model) if model is not None else None

    async def list_group_ids(self) -> list[int]:
        result = await self._session.execute(select(Group.id).order_by(Group.id))
        return [row[0] for row in result.all()]

    async def get_by_name(self, name: str) -> GroupInfo | None:
        query = (
            select(Group)
            .options(selectinload(Group.memberships).selectinload(GroupMembership.weight))
            .where(Group.name == name)
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return map_group(model) if model is not None else None

    async def get_active_membership(self, user_id: int) -> MembershipInfo | None:
        query = (
            select(GroupMembership)
            .options(selectinload(GroupMembership.weight))
            .where(GroupMembership.user_id == user_id, GroupMembership.left_at.is_(None))
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return map_membership(model) if model is not None else None

    async def get_active_membership_in_group(
        self, *, group_id: int, user_id: int
    ) -> MembershipInfo | None:
        query = (
            select(GroupMembership)
            .options(selectinload(GroupMembership.weight))
            .where(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == user_id,
                GroupMembership.left_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return map_membership(model) if model is not None else None

    async def list_active_memberships(self, group_id: int) -> list[MembershipInfo]:
        query = (
            select(GroupMembership)
            .options(selectinload(GroupMembership.weight))
            .where(GroupMembership.group_id == group_id, GroupMembership.left_at.is_(None))
        )
        result = await self._session.execute(query)
        return [map_membership(item) for item in result.scalars().all()]

    async def create_group(
        self,
        *,
        name: str,
        join_secret: str,
        owner_user_id: int,
        sprint_start_weekday: Weekday,
        sprint_duration_days: int,
        timezone: str,
        created_at: date,
    ) -> GroupInfo:
        model = Group(
            name=name,
            join_secret=join_secret,
            owner_user_id=owner_user_id,
            sprint_start_weekday=sprint_start_weekday,
            sprint_duration_days=sprint_duration_days,
            timezone=timezone,
            created_at=datetime.combine(created_at, time.min, tzinfo=UTC),
        )
        self._session.add(model)
        await self._session.flush()
        created = await self._fetch_group(group_id=model.id)
        if created is None:
            raise NotFoundError("Group was not found")
        return map_group(created)

    async def create_membership(self, *, group_id: int, user_id: int) -> MembershipInfo:
        model = GroupMembership(group_id=group_id, user_id=user_id)
        self._session.add(model)
        await self._session.flush()
        return MembershipInfo(
            id=model.id,
            group_id=model.group_id,
            user_id=model.user_id,
            left_at=model.left_at,
            weight_percent=None,
        )

    async def ensure_balance(self, *, group_id: int, user_id: int) -> Decimal:
        query = select(Balance).where(Balance.group_id == group_id, Balance.user_id == user_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            model = Balance(group_id=group_id, user_id=user_id)
            self._session.add(model)
            await self._session.flush()
        return model.current_balance

    async def set_owner(self, *, group_id: int, owner_user_id: int) -> None:
        model = await self._require_group_model(group_id)
        model.owner_user_id = owner_user_id
        await self._session.flush()

    async def set_group_balance(self, *, group_id: int, balance: Decimal) -> None:
        model = await self._require_group_model(group_id)
        model.balance = balance
        await self._session.flush()

    async def deactivate_membership(self, membership_id: int, *, left_at: datetime) -> None:
        model = await self._session.get(GroupMembership, membership_id)
        if model is None:
            raise NotFoundError("Membership was not found")
        model.left_at = left_at
        await self._session.flush()

    async def replace_weights(
        self, *, group_id: int, weights_by_user_id: dict[int, Decimal]
    ) -> None:
        query = (
            select(GroupMembership)
            .options(selectinload(GroupMembership.weight))
            .where(GroupMembership.group_id == group_id, GroupMembership.left_at.is_(None))
        )
        result = await self._session.execute(query)
        memberships = result.scalars().all()
        for membership in memberships:
            desired_weight = weights_by_user_id.get(membership.user_id)
            if desired_weight is None:
                continue
            if membership.weight is None:
                membership.weight = GroupMemberWeight(weight_percent=desired_weight)
            else:
                membership.weight.weight_percent = desired_weight
        await self._session.flush()

    async def update_settings(
        self,
        *,
        group_id: int,
        join_secret: str | None,
        sprint_start_weekday: Weekday | None,
        sprint_duration_days: int | None = None,
    ) -> GroupInfo:
        model = await self._require_group_model(group_id)
        if join_secret is not None:
            model.join_secret = join_secret
        if sprint_start_weekday is not None:
            model.sprint_start_weekday = sprint_start_weekday
        if sprint_duration_days is not None:
            model.sprint_duration_days = sprint_duration_days
        await self._session.flush()
        await self._session.refresh(model)
        return map_group(model)

    async def list_member_balances(self, group_id: int) -> dict[int, Decimal]:
        query = select(Balance).where(Balance.group_id == group_id)
        result = await self._session.execute(query)
        return {model.user_id: model.current_balance for model in result.scalars().all()}

    async def get_balance(self, *, group_id: int, user_id: int) -> Decimal:
        query = select(Balance).where(Balance.group_id == group_id, Balance.user_id == user_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            raise NotFoundError("Balance was not found")
        return model.current_balance

    async def apply_balance_delta(
        self, *, group_id: int, user_id: int, amount_delta: Decimal
    ) -> Decimal:
        query = select(Balance).where(Balance.group_id == group_id, Balance.user_id == user_id)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        if model is None:
            model = Balance(group_id=group_id, user_id=user_id, current_balance=Decimal("0"))
            self._session.add(model)
            await self._session.flush()
        model.current_balance += amount_delta
        await self._session.flush()
        return model.current_balance

    async def transfer_balance(
        self,
        *,
        group_id: int,
        sender_user_id: int,
        recipient_user_id: int,
        amount: Decimal,
    ) -> tuple[Decimal, Decimal]:
        query = (
            select(Balance)
            .where(
                Balance.group_id == group_id,
                Balance.user_id.in_((sender_user_id, recipient_user_id)),
            )
            .order_by(Balance.user_id)
            .with_for_update()
        )
        result = await self._session.execute(query)
        balances = {model.user_id: model for model in result.scalars().all()}
        sender = balances.get(sender_user_id)
        recipient = balances.get(recipient_user_id)
        if sender is None or recipient is None:
            raise NotFoundError("Balance was not found")
        if sender.current_balance < amount:
            raise BusinessRuleViolation("Insufficient balance for this transfer")
        sender.current_balance -= amount
        recipient.current_balance += amount
        await self._session.flush()
        return sender.current_balance, recipient.current_balance

    async def _fetch_group(self, *, group_id: int) -> Group | None:
        query = (
            select(Group)
            .options(selectinload(Group.memberships).selectinload(GroupMembership.weight))
            .where(Group.id == group_id)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def _require_group_model(self, group_id: int) -> Group:
        model = await self._fetch_group(group_id=group_id)
        if model is None:
            raise NotFoundError("Group was not found")
        return model
