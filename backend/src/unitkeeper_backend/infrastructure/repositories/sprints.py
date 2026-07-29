from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from db.enums import BalanceTransactionAccountType, BalanceTransactionType, SprintRunStatus
from db.models import BalanceTransaction, SprintMemberResult, SprintRun
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unitkeeper_backend.application.models import (
    BalanceTransactionInfo,
    SprintMemberResultInfo,
    SprintRunInfo,
)
from unitkeeper_backend.infrastructure.repositories.mappers import map_sprint_run


class SqlAlchemySprintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_sprint_run(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
    ) -> SprintRunInfo | None:
        query = (
            select(SprintRun)
            .options(selectinload(SprintRun.member_results))
            .where(
                SprintRun.group_id == group_id,
                SprintRun.period_start == period_start,
                SprintRun.period_end == period_end,
            )
        )
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return map_sprint_run(model) if model is not None else None

    async def create_sprint_run(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
        total_planned_units: Decimal,
        total_completed_units: Decimal,
        bonus_units: Decimal,
        balance_delta: Decimal,
        closed_at: datetime,
        member_results: list[SprintMemberResultInfo],
    ) -> SprintRunInfo:
        model = SprintRun(
            group_id=group_id,
            period_start=period_start,
            period_end=period_end,
            status=SprintRunStatus.CLOSED,
            total_planned_units=total_planned_units,
            total_completed_units=total_completed_units,
            bonus_units=bonus_units,
            balance_delta=balance_delta,
            closed_at=closed_at,
        )
        self._session.add(model)
        await self._session.flush()

        for item in member_results:
            self._session.add(
                SprintMemberResult(
                    sprint_run_id=model.id,
                    user_id=item.user_id,
                    planned_units=item.planned_units,
                    completed_units=item.completed_units,
                    efficiency_percent=item.efficiency_percent,
                    bonus_units=item.bonus_units,
                    balance_delta=item.balance_delta,
                    balance_after=item.balance_after,
                )
            )

        await self._session.flush()
        await self._session.refresh(model)
        refreshed = await self.get_sprint_run(
            group_id=group_id,
            period_start=period_start,
            period_end=period_end,
        )
        assert refreshed is not None
        return refreshed

    async def add_balance_transaction(
        self,
        *,
        group_id: int,
        user_id: int | None,
        transaction_type: BalanceTransactionType,
        amount_delta: Decimal,
        description: str,
        transaction_group_id: UUID,
        account_type: BalanceTransactionAccountType = BalanceTransactionAccountType.USER,
        sprint_run_id: int | None = None,
        task_log_id: int | None = None,
        counterparty_user_id: int | None = None,
    ) -> None:
        self._session.add(
            BalanceTransaction(
                group_id=group_id,
                account_type=account_type,
                user_id=user_id,
                transaction_type=transaction_type,
                amount_delta=amount_delta,
                description=description,
                transaction_group_id=transaction_group_id,
                sprint_run_id=sprint_run_id,
                task_log_id=task_log_id,
                counterparty_user_id=counterparty_user_id,
            )
        )
        await self._session.flush()

    async def list_balance_transactions(
        self,
        *,
        group_id: int,
        user_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[BalanceTransactionInfo], int]:
        query = (
            select(BalanceTransaction)
            .where(BalanceTransaction.group_id == group_id, BalanceTransaction.user_id == user_id)
            .order_by(BalanceTransaction.created_at.desc(), BalanceTransaction.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        items: list[BalanceTransactionInfo] = []
        for model in result.scalars().all():
            if model.user_id is None:
                continue
            items.append(
                BalanceTransactionInfo(
                    id=model.id,
                    group_id=model.group_id,
                    user_id=model.user_id,
                    transaction_type=model.transaction_type,
                    amount_delta=model.amount_delta,
                    counterparty_user_id=model.counterparty_user_id,
                    description=model.description,
                    created_at=model.created_at,
                )
            )
        total_query = (
            select(func.count())
            .select_from(BalanceTransaction)
            .where(
                BalanceTransaction.group_id == group_id,
                BalanceTransaction.user_id == user_id,
            )
        )
        total = (await self._session.execute(total_query)).scalar_one()
        return items, total
