from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from uuid import uuid4

from db.enums import BalanceTransactionAccountType, BalanceTransactionType, SprintRunStatus

from unitkeeper_backend.application.models import (
    CompletedTaskBreakdownItem,
    SprintMemberResultInfo,
    SprintRunInfo,
    TempResults,
)
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.domain.errors import BusinessRuleViolation, NotFoundError
from unitkeeper_backend.domain.services.sprint_math import (
    ZERO,
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
            today=self._clock.today(),
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
            performer_user_id=user_id,
            window_start=window.starts_at,
            window_end_exclusive=window.ends_before,
        )
        task_by_id = {task.id: task for task in tasks}
        completed = ZERO
        counters: dict[int, int] = defaultdict(int)
        for log in logs:
            task = task_by_id.get(log.task_id)
            if task is None:
                continue
            counters[task.id] += 1
            completed += task.unit_cost

        breakdown = [
            CompletedTaskBreakdownItem(
                task_id=task_id,
                title=task_by_id[task_id].title,
                completed_count=count,
                completed_units=quantize(task_by_id[task_id].unit_cost * count),
            )
            for task_id, count in sorted(
                counters.items(), key=lambda item: task_by_id[item[0]].title.lower()
            )
        ]
        return TempResults(
            period_start=window.period_start,
            period_end=window.period_end,
            planned_units=quantize(planned),
            completed_units=quantize(completed),
            progress_percent=progress_percent(
                completed_units=completed, planned_units_total=planned
            ),
            breakdown=breakdown,
        )

    async def close_current_sprint(self, *, group_id: int) -> SprintRunInfo:
        group = await self._uow.groups.get_by_id(group_id)
        if group is None:
            raise NotFoundError("Group was not found")

        window = current_sprint_window(
            today=self._clock.today(),
            start_weekday=group.sprint_start_weekday,
            duration_days=group.sprint_duration_days,
            anchor=group.created_at,
        )
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
