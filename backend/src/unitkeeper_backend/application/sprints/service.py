from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from db.enums import (
    BalanceTransactionAccountType,
    BalanceTransactionType,
    SprintRunStatus,
    TaskLogStatus,
)

from unitkeeper_backend.application.models import (
    CompletedTaskBreakdownItem,
    GroupProgressInfo,
    SprintMemberResultInfo,
    SprintRunInfo,
    TempResults,
)
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.application.timezones import resolve_group_zone
from unitkeeper_backend.domain.errors import BusinessRuleViolation, NotFoundError
from unitkeeper_backend.domain.services.sprint_math import (
    ZERO,
    SprintWindow,
    current_sprint_window,
    planned_units,
    progress_percent,
    quantize,
)


class SprintService:
    def __init__(self, *, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def get_temp_results(self, *, user_id: int, group_id: int) -> TempResults:
        group = await self._uow.groups.get_by_id(group_id)
        if group is None:
            raise NotFoundError("Group was not found")
        membership = await self._uow.groups.get_active_membership_in_group(
            group_id=group_id, user_id=user_id
        )
        if membership is None or membership.weight_percent is None:
            raise NotFoundError("Active membership was not found")

        window = current_sprint_window(
            now=self._clock.now(),
            zone=resolve_group_zone(group_id=group.id, timezone_name=group.timezone),
            start_weekday=group.sprint_start_weekday,
            duration_days=group.sprint_duration_days,
            anchor=group.created_at,
        )
        tasks = await self._uow.tasks.list_tasks(group_id=group_id, active_only=True)
        total_task_units = sum(
            (task.unit_cost * task.frequency_per_sprint for task in tasks),
            start=ZERO,
        )
        planned = planned_units(
            total_task_units=total_task_units, weight_percent=membership.weight_percent
        )
        logs = await self._uow.tasks.list_completed_logs_in_window(
            group_id=group_id,
            performer_user_id=None,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        task_by_id = {task.id: task for task in tasks}
        completed = ZERO
        group_completed = ZERO
        counters: dict[tuple[int, int], int] = defaultdict(int)
        last_completed_at: dict[tuple[int, int], datetime] = {}
        for log in logs:
            task = task_by_id.get(log.task_id)
            if task is None:
                continue
            group_completed += task.unit_cost
            key = (task.id, log.performer_user_id)
            counters[key] += 1
            completed_at = log.decided_at or log.created_at
            previous_completed_at = last_completed_at.get(key)
            if previous_completed_at is None or completed_at > previous_completed_at:
                last_completed_at[key] = completed_at
            if log.performer_user_id == user_id:
                completed += task.unit_cost

        performers = await self._uow.users.list_by_ids(
            sorted({performer_id for _, performer_id in counters})
        )
        performer_by_id = {performer.id: performer for performer in performers}

        breakdown = [
            CompletedTaskBreakdownItem(
                task_id=task_id,
                title=task_by_id[task_id].title,
                completed_count=count,
                completed_units=quantize(task_by_id[task_id].unit_cost * count),
                performer_user_id=performer_id,
                performer_first_name=performer_by_id[performer_id].first_name
                if performer_id in performer_by_id
                else None,
                performer_username=performer_by_id[performer_id].username
                if performer_id in performer_by_id
                else None,
                last_completed_at=last_completed_at[(task_id, performer_id)],
                performer_photo_url=(
                    performer_by_id[performer_id].photo_url
                    if performer_id in performer_by_id
                    else None
                ),
            )
            for (task_id, performer_id), count in counters.items()
        ]
        breakdown.sort(key=lambda item: item.last_completed_at, reverse=True)
        group_progress = GroupProgressInfo(
            planned_units=quantize(total_task_units),
            completed_units=quantize(group_completed),
            progress_percent=progress_percent(
                completed_units=group_completed, planned_units_total=total_task_units
            ),
        )
        return TempResults(
            period_start=window.period_start,
            period_end=window.period_end,
            planned_units=quantize(planned),
            completed_units=quantize(completed),
            progress_percent=progress_percent(
                completed_units=completed, planned_units_total=planned
            ),
            breakdown=breakdown,
            group=group_progress,
        )

    async def close_current_sprint(
        self,
        *,
        group_id: int,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> SprintRunInfo:
        """Settle one sprint window for ``group_id``.

        The scheduler passes the exact period it discovered, so a catch-up pass
        settles the window it meant to settle rather than whichever one happens
        to be current by the time the close runs. With no explicit period — the
        manual-close path — this targets the group's most recently *ended*
        window, never the running one. Either way, a window that has not fully
        ended in group-local time is refused.
        """
        group = await self._uow.groups.get_by_id(group_id)
        if group is None:
            raise NotFoundError("Group was not found")

        now = self._clock.now()
        zone = resolve_group_zone(group_id=group.id, timezone_name=group.timezone)
        if period_start is not None and period_end is not None:
            window = SprintWindow(period_start=period_start, period_end=period_end, zone=zone)
        else:
            current = current_sprint_window(
                now=now,
                zone=zone,
                start_weekday=group.sprint_start_weekday,
                duration_days=group.sprint_duration_days,
                anchor=group.created_at,
            )
            # ``current`` contains ``now``, so it is by definition still running.
            # The newest settleable window is the one immediately before it.
            window = current.shifted(-1)
            if window.period_end < group.created_at:
                raise BusinessRuleViolation("Sprint window has not ended yet and cannot be closed")

        if not window.has_ended_at(now):
            raise BusinessRuleViolation("Sprint window has not ended yet and cannot be closed")

        existing = await self._uow.sprints.get_sprint_run(
            group_id=group_id,
            period_start=window.period_start,
            period_end=window.period_end,
        )
        if existing is not None and existing.status is SprintRunStatus.CLOSED:
            raise BusinessRuleViolation("Current sprint has already been closed")

        tasks = await self._uow.tasks.list_tasks(group_id=group_id, active_only=True)
        logs = await self._uow.tasks.list_completed_logs_in_window(
            group_id=group_id,
            performer_user_id=None,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        memberships = await self._uow.groups.list_active_memberships(group_id)
        if not memberships:
            raise BusinessRuleViolation("Cannot close a sprint for a group without active members")

        # A log still pending when its own window closes can never be approved
        # into that window's stats, so auto-reject it. Scope this to the window
        # being settled: a catch-up close of an older window must leave marks
        # made during a later, still-running window pending and approvable.
        pending_logs = await self._uow.tasks.list_task_logs(
            group_id=group_id,
            statuses=[TaskLogStatus.PENDING],
            limit=10_000,
            offset=0,
        )
        for pending_log in pending_logs:
            if not window.starts_at <= pending_log.created_at < window.ends_before:
                continue
            await self._uow.tasks.reject_task_log(
                log_id=pending_log.id,
                approver_user_id=None,
                decided_at=now,
                rejection_reason="Спринт закрылся без подтверждения",
            )

        task_by_id = {task.id: task for task in tasks}
        completed_by_user: dict[int, Decimal] = defaultdict(lambda: ZERO)
        for log in logs:
            task = task_by_id.get(log.task_id)
            if task is None:
                continue
            completed_by_user[log.performer_user_id] += task.unit_cost

        total_task_units = sum(
            (task.unit_cost * task.frequency_per_sprint for task in tasks), start=ZERO
        )
        total_completed = sum(completed_by_user.values(), start=ZERO)
        total_planned = ZERO
        bonus_units = (
            quantize(total_task_units * Decimal("0.25"))
            if total_completed >= total_task_units and total_task_units > ZERO
            else ZERO
        )
        member_results: list[SprintMemberResultInfo] = []

        for membership in sorted(memberships, key=lambda item: item.user_id):
            weight = membership.weight_percent or ZERO
            planned_for_user = planned_units(
                total_task_units=total_task_units, weight_percent=weight
            )
            completed_for_user = quantize(completed_by_user.get(membership.user_id, ZERO))
            efficiency = progress_percent(
                completed_units=completed_for_user, planned_units_total=planned_for_user
            )
            bonus_for_user = planned_units(total_task_units=bonus_units, weight_percent=weight)
            balance_delta = quantize(completed_for_user - planned_for_user + bonus_for_user)
            balance_after = await self._uow.groups.apply_balance_delta(
                group_id=group_id,
                user_id=membership.user_id,
                amount_delta=balance_delta,
            )
            member_results.append(
                SprintMemberResultInfo(
                    user_id=membership.user_id,
                    planned_units=planned_for_user,
                    completed_units=completed_for_user,
                    efficiency_percent=efficiency,
                    bonus_units=bonus_for_user,
                    balance_delta=balance_delta,
                    balance_after=balance_after,
                )
            )

        total_planned = sum((item.planned_units for item in member_results), start=ZERO)
        balance_delta = quantize(total_completed - total_planned)
        await self._uow.groups.set_group_balance(group_id=group_id, balance=balance_delta)

        sprint_run = await self._uow.sprints.create_sprint_run(
            group_id=group_id,
            period_start=window.period_start,
            period_end=window.period_end,
            total_planned_units=quantize(total_planned),
            total_completed_units=quantize(total_completed),
            bonus_units=bonus_units,
            balance_delta=balance_delta,
            closed_at=self._clock.now(),
            member_results=member_results,
        )
        pool_amount = sum((item.balance_delta for item in member_results), start=ZERO)
        if pool_amount != ZERO or any(item.balance_delta != ZERO for item in member_results):
            settlement_group_id = uuid4()
            description = f"Sprint settlement for {window.period_start}..{window.period_end}"
            if pool_amount != ZERO:
                await self._uow.sprints.add_balance_transaction(
                    group_id=group_id,
                    user_id=None,
                    account_type=BalanceTransactionAccountType.GROUP_POOL,
                    transaction_type=BalanceTransactionType.SPRINT_SETTLEMENT,
                    amount_delta=-pool_amount,
                    description=description,
                    transaction_group_id=settlement_group_id,
                    sprint_run_id=sprint_run.id,
                )
            for item in member_results:
                if item.balance_delta == ZERO:
                    continue
                await self._uow.sprints.add_balance_transaction(
                    group_id=group_id,
                    user_id=item.user_id,
                    account_type=BalanceTransactionAccountType.USER,
                    transaction_type=BalanceTransactionType.SPRINT_SETTLEMENT,
                    amount_delta=item.balance_delta,
                    description=description,
                    transaction_group_id=settlement_group_id,
                    sprint_run_id=sprint_run.id,
                )
        await self._uow.commit()
        return sprint_run
