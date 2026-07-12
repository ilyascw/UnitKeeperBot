from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from db.enums import NotificationEventType, Weekday
from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.models import (
    CurrentContext,
    GroupCardInfo,
    GroupInfo,
    MemberCardInfo,
)
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.domain.errors import (
    AuthorizationError,
    BusinessRuleViolation,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from unitkeeper_backend.domain.services.sprint_math import (
    ZERO,
    current_sprint_window,
    distribute_equally,
    validate_member_weights,
)


class GroupService:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        context_service: CurrentContextService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._context_service = context_service
        self._clock = clock

    async def create_group(
        self,
        *,
        user_id: int,
        name: str,
        join_secret: str,
        sprint_start_weekday: Weekday,
        sprint_duration_days: int,
        timezone: str,
    ) -> CurrentContext:
        await self._ensure_user_has_no_group(user_id)
        self._validate_name(name)
        self._validate_join_secret(join_secret)
        self._validate_sprint_duration(sprint_duration_days)

        existing = await self._uow.groups.get_by_name(name)
        if existing is not None:
            raise ConflictError("Group name is already taken")

        group = await self._uow.groups.create_group(
            name=name,
            join_secret=join_secret,
            owner_user_id=user_id,
            sprint_start_weekday=sprint_start_weekday,
            sprint_duration_days=sprint_duration_days,
            timezone=timezone,
            created_at=self._clock.today(),
        )
        await self._uow.groups.create_membership(group_id=group.id, user_id=user_id)
        await self._uow.groups.replace_weights(group_id=group.id, weights_by_user_id={user_id: Decimal("100.00")})
        await self._uow.groups.ensure_balance(group_id=group.id, user_id=user_id)
        await self._uow.commit()
        return await self._context_service.resolve(user_id)

    async def join_group(self, *, user_id: int, group_name: str, join_secret: str) -> CurrentContext:
        await self._ensure_user_has_no_group(user_id)
        self._validate_name(group_name)
        self._validate_join_secret(join_secret)

        group = await self._uow.groups.get_by_name(group_name)
        if group is None or group.join_secret != join_secret:
            raise NotFoundError("Group with provided name and join secret was not found")

        await self._uow.groups.create_membership(group_id=group.id, user_id=user_id)
        await self._uow.groups.ensure_balance(group_id=group.id, user_id=user_id)
        await self._rebalance_group(group.id)
        memberships = await self._uow.groups.list_active_memberships(group.id)
        for membership in memberships:
            if membership.user_id == user_id:
                continue
            await self._uow.notifications.enqueue(
                event_type=NotificationEventType.REMINDER,
                recipient_user_id=membership.user_id,
                group_id=group.id,
                payload={
                    "kind": "membership_event",
                    "group_name": group.name,
                    "message": "В группу вступил новый участник.",
                },
                deep_link_path="/group",
            )
        await self._uow.commit()
        return await self._context_service.resolve(user_id)

    async def leave_group(self, *, user_id: int, left_at: datetime) -> None:
        membership = await self._uow.groups.get_active_membership(user_id)
        if membership is None:
            raise BusinessRuleViolation("User does not have an active group")

        group = await self._uow.groups.get_by_id(membership.group_id)
        if group is None:
            raise NotFoundError("Active group was not found")

        await self._uow.groups.deactivate_membership(membership.id, left_at=left_at)
        remaining = await self._uow.groups.list_active_memberships(group.id)

        next_owner_id = None
        if group.owner_user_id == user_id and remaining:
            next_owner_id = sorted(member.user_id for member in remaining)[0]
            await self._uow.groups.set_owner(group_id=group.id, owner_user_id=next_owner_id)

        if remaining:
            await self._uow.groups.replace_weights(
                group_id=group.id,
                weights_by_user_id=distribute_equally([member.user_id for member in remaining]),
            )
            for member in remaining:
                owner_changed = member.user_id == next_owner_id
                await self._uow.notifications.enqueue(
                    event_type=NotificationEventType.REMINDER,
                    recipient_user_id=member.user_id,
                    group_id=group.id,
                    payload={
                        "kind": "group_event" if owner_changed else "membership_event",
                        "group_name": group.name,
                        "message": (
                            "Вы назначены новым владельцем группы."
                            if owner_changed
                            else "Один из участников покинул группу."
                        ),
                    },
                    deep_link_path="/group",
                )

        await self._uow.commit()

    async def get_current_group(self, *, user_id: int) -> GroupInfo:
        context = await self._context_service.resolve(user_id)
        if context.group is None:
            raise NotFoundError("User has no active group")
        return context.group

    async def get_current_group_card(self, *, user_id: int) -> GroupCardInfo:
        group, memberships = await self._require_active_group(user_id)
        members = await self._build_member_cards(group=group, memberships=memberships)
        window = current_sprint_window(
            today=self._clock.today(),
            start_weekday=group.sprint_start_weekday,
            duration_days=group.sprint_duration_days,
            anchor=group.created_at,
        )
        sprint_ends_at = datetime.combine(
            window.period_end + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )
        return GroupCardInfo(
            id=group.id,
            name=group.name,
            owner_user_id=group.owner_user_id,
            sprint_start_weekday=group.sprint_start_weekday,
            sprint_duration_days=group.sprint_duration_days,
            timezone=group.timezone,
            group_balance=group.balance,
            sprint_period_start=window.period_start,
            sprint_period_end=window.period_end,
            sprint_ends_at=sprint_ends_at,
            members=members,
            join_secret=group.join_secret if group.owner_user_id == user_id else None,
        )

    async def list_current_group_members(self, *, user_id: int) -> list[MemberCardInfo]:
        group, memberships = await self._require_active_group(user_id)
        return await self._build_member_cards(group=group, memberships=memberships)

    async def update_current_group_settings(
        self,
        *,
        user_id: int,
        join_secret: str | None,
        sprint_start_weekday: Weekday | None,
        sprint_duration_days: int | None,
    ) -> GroupInfo:
        group, _ = await self._require_owner_group(user_id)
        if join_secret is None and sprint_start_weekday is None and sprint_duration_days is None:
            raise ValidationError("At least one field must be provided")
        if join_secret is not None:
            self._validate_join_secret(join_secret)
        if sprint_duration_days is not None:
            self._validate_sprint_duration(sprint_duration_days)
        return await self._uow.groups.update_settings(
            group_id=group.id,
            join_secret=join_secret,
            sprint_start_weekday=sprint_start_weekday,
            sprint_duration_days=sprint_duration_days,
        )

    async def update_current_group_weights(
        self,
        *,
        user_id: int,
        weights_by_user_id: dict[int, Decimal],
    ) -> list[MemberCardInfo]:
        group, memberships = await self._require_owner_group(user_id)
        active_ids = [membership.user_id for membership in memberships]
        validated = validate_member_weights(
            active_user_ids=active_ids,
            weights_by_user_id=weights_by_user_id,
        )
        await self._uow.groups.replace_weights(group_id=group.id, weights_by_user_id=validated)
        await self._uow.commit()
        refreshed = await self._uow.groups.list_active_memberships(group.id)
        return await self._build_member_cards(group=group, memberships=refreshed)

    async def _require_active_group(self, user_id: int):
        context = await self._context_service.resolve(user_id)
        if context.group is None:
            raise NotFoundError("User has no active group")
        memberships = await self._uow.groups.list_active_memberships(context.group.id)
        return context.group, memberships

    async def _require_owner_group(self, user_id: int):
        group, memberships = await self._require_active_group(user_id)
        if group.owner_user_id != user_id:
            raise AuthorizationError("Only the group owner can perform this action")
        return group, memberships

    async def _build_member_cards(self, *, group: GroupInfo, memberships) -> list[MemberCardInfo]:
        if not memberships:
            return []
        user_ids = [membership.user_id for membership in memberships]
        profiles = await self._uow.users.list_by_ids(user_ids)
        profile_by_id = {profile.id: profile for profile in profiles}
        balances = await self._uow.groups.list_member_balances(group.id)
        cards: list[MemberCardInfo] = []
        for membership in sorted(memberships, key=lambda item: item.user_id):
            profile = profile_by_id.get(membership.user_id)
            cards.append(
                MemberCardInfo(
                    user_id=membership.user_id,
                    username=profile.username if profile else None,
                    first_name=profile.first_name if profile else None,
                    last_name=profile.last_name if profile else None,
                    weight_percent=membership.weight_percent or ZERO,
                    balance=balances.get(membership.user_id, ZERO),
                    is_owner=membership.user_id == group.owner_user_id,
                )
            )
        return cards

    async def _ensure_user_has_no_group(self, user_id: int) -> None:
        membership = await self._uow.groups.get_active_membership(user_id)
        if membership is not None:
            raise BusinessRuleViolation("Leave the current group before creating or joining another one")

    async def _rebalance_group(self, group_id: int) -> None:
        memberships = await self._uow.groups.list_active_memberships(group_id)
        weights = distribute_equally([membership.user_id for membership in memberships])
        await self._uow.groups.replace_weights(group_id=group_id, weights_by_user_id=weights)

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name.strip():
            raise ValidationError("Group name is required")

    @staticmethod
    def _validate_join_secret(join_secret: str) -> None:
        if len(join_secret.strip()) < 3:
            raise ValidationError("Join secret must be at least 3 characters long")

    @staticmethod
    def _validate_sprint_duration(duration_days: int) -> None:
        if duration_days <= 0 or duration_days % 7 != 0:
            raise ValidationError("Sprint duration must be positive and divisible by 7")
