"""Concrete sprint-close discovery/execution, driving the existing close use case.

This module contains the only logic that decides *when* a group's sprint is due
for automatic closing and *how* duplicate runs are made safe. It never
duplicates sprint-close business rules: all of that stays in
``SprintService.close_current_sprint`` (application/sprints/service.py). This
class is purely an adapter between the scheduler-facing ``SprintCloser``
protocol (application/jobs/scheduler.py) and that existing service.

Timezone policy: due-ness and "today" are evaluated in UTC, matching
``UtcClock`` and ``domain.services.sprint_math.current_sprint_window`` (which
already anchor sprint windows to UTC midnight). Per-group ``timezone`` values
are not yet consulted here, consistent with the rest of the sprint-math
domain code.
"""

from __future__ import annotations

import logging

from unitkeeper_backend.application.jobs.scheduler import ClosedSprint
from unitkeeper_backend.application.jobs.notifications import SprintMemberReport
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.domain.errors import BusinessRuleViolation, NotFoundError
from unitkeeper_backend.domain.services.sprint_math import current_sprint_window

logger = logging.getLogger(__name__)


async def list_due_group_ids(*, uow: UnitOfWork, clock: Clock) -> list[int]:
    """Return ids of groups whose current sprint window ends today (UTC).

    A group is "due" on the last calendar day of its running sprint window, so
    the job can be scheduled to run once a day and still close every sprint on
    time. Groups that are not due are skipped (and logged as such); actual
    duplicate-close protection is handled downstream by
    ``SprintCloseRunner.close_due_sprint``.
    """
    today = clock.today()
    due_group_ids: list[int] = []
    for group_id in await uow.groups.list_group_ids():
        group = await uow.groups.get_by_id(group_id)
        if group is None:
            continue
        window = current_sprint_window(
            today=today,
            start_weekday=group.sprint_start_weekday,
            duration_days=group.sprint_duration_days,
        )
        if window.period_end != today:
            logger.debug(
                "sprint_close.skip_not_due group_id=%s period_end=%s today=%s",
                group_id,
                window.period_end,
                today,
            )
            continue
        due_group_ids.append(group_id)
    return due_group_ids


class SprintCloseRunner:
    """Adapts ``SprintService.close_current_sprint`` to the ``SprintCloser`` protocol."""

    def __init__(self, *, sprint_service: SprintService, uow: UnitOfWork) -> None:
        self._sprint_service = sprint_service
        self._uow = uow

    async def close_due_sprint(self, *, group_id: int, correlation_id: str) -> ClosedSprint | None:
        try:
            sprint_run = await self._sprint_service.close_current_sprint(group_id=group_id)
        except BusinessRuleViolation:
            logger.info(
                "sprint_close.duplicate_skipped group_id=%s correlation_id=%s",
                group_id,
                correlation_id,
            )
            return None
        except NotFoundError:
            logger.warning(
                "sprint_close.group_not_found group_id=%s correlation_id=%s",
                group_id,
                correlation_id,
            )
            return None

        group = await self._uow.groups.get_by_id(group_id)
        group_name = group.name if group is not None else str(group_id)
        owner_user_id = group.owner_user_id if group is not None else 0
        period = f"{sprint_run.period_start.isoformat()}..{sprint_run.period_end.isoformat()}"
        reports = [
            SprintMemberReport(
                user_id=item.user_id,
                planned_units=str(item.planned_units),
                completed_units=str(item.completed_units),
                balance_delta=str(item.balance_delta),
            )
            for item in sprint_run.member_results
        ]
        logger.info(
            "sprint_close.closed group_id=%s period=%s correlation_id=%s",
            group_id,
            period,
            correlation_id,
        )
        return ClosedSprint(
            group_id=group_id,
            group_name=group_name,
            owner_user_id=owner_user_id,
            period=period,
            planned_units=str(sprint_run.total_planned_units),
            completed_units=str(sprint_run.total_completed_units),
            reports=reports,
        )
