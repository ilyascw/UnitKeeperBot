"""Concrete sprint-close discovery/execution, driving the existing close use case.

This module contains the only logic that decides *which* sprint windows are due
for automatic closing and *how* duplicate runs are made safe. It never
duplicates sprint-close business rules: all of that stays in
``SprintService.close_current_sprint`` (application/sprints/service.py). This
class is purely an adapter between the scheduler-facing ``SprintCloser``
protocol (application/jobs/scheduler.py) and that existing service.

Timezone policy: every window is evaluated in the group's own stored IANA
``timezone``. A window is due once the current instant has reached its end
boundary — ``00:00`` local on the day after ``period_end`` — so groups in
different zones each settle near their own local boundary. A stored timezone
that cannot be resolved degrades to UTC with a warning (see
``application/timezones.py``) rather than stalling the pass.
"""

from __future__ import annotations

import logging
from datetime import date

from db.enums import SprintRunStatus

from unitkeeper_backend.application.jobs.notifications import SprintMemberReport
from unitkeeper_backend.application.jobs.scheduler import ClosedSprint, DueSprintWindow
from unitkeeper_backend.application.ports import Clock, UnitOfWork
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.application.timezones import resolve_group_zone
from unitkeeper_backend.domain.errors import BusinessRuleViolation, NotFoundError
from unitkeeper_backend.domain.services.sprint_math import current_sprint_window

logger = logging.getLogger(__name__)

# How far back a single pass will look for windows that ended without being
# settled. Bounds the walk so a group that has never closed degrades to "the
# last few windows, loudly" instead of replaying its whole history.
DEFAULT_LOOKBACK_WINDOWS = 8


async def list_due_sprint_windows(
    *, uow: UnitOfWork, clock: Clock, lookback_windows: int = DEFAULT_LOOKBACK_WINDOWS
) -> list[DueSprintWindow]:
    """Return every ended, unsettled sprint window, oldest first per group.

    Due-ness is elapsed time (``now >= window.ends_before``) rather than
    calendar equality, which is what makes catch-up fall out for free: a window
    that ended three days ago still satisfies the comparison. For each group the
    walk steps backward from the current window while windows have ended and
    carry no ``CLOSED`` sprint run, stopping at the lookback cap or the group's
    ``created_at``, then emits what it found in chronological order.
    """
    now = clock.now()
    due: list[DueSprintWindow] = []
    for group_id in await uow.groups.list_group_ids():
        group = await uow.groups.get_by_id(group_id)
        if group is None:
            continue
        current = current_sprint_window(
            now=now,
            zone=resolve_group_zone(group_id=group.id, timezone_name=group.timezone),
            start_weekday=group.sprint_start_weekday,
            duration_days=group.sprint_duration_days,
            anchor=group.created_at,
        )
        # The current window contains ``now`` by construction, so it has not
        # ended; the newest window that can be due is the one before it.
        window = current.shifted(-1)

        pending: list[DueSprintWindow] = []
        steps = 0
        while (
            steps < lookback_windows
            and window.has_ended_at(now)
            # Stop before the group's own first window: anything ending earlier
            # predates the group and was never a sprint it could have run.
            and window.period_end >= group.created_at
        ):
            existing = await uow.sprints.get_sprint_run(
                group_id=group_id,
                period_start=window.period_start,
                period_end=window.period_end,
            )
            if existing is not None and existing.status is SprintRunStatus.CLOSED:
                break
            pending.append(
                DueSprintWindow(
                    group_id=group_id,
                    period_start=window.period_start,
                    period_end=window.period_end,
                )
            )
            window = window.shifted(-1)
            steps += 1
        else:
            if steps >= lookback_windows:
                logger.warning(
                    "sprint_close.lookback_cap_reached group_id=%s cap=%s oldest_period_start=%s",
                    group_id,
                    lookback_windows,
                    window.period_start,
                )

        if not pending:
            logger.debug("sprint_close.skip_not_due group_id=%s now=%s", group_id, now)
            continue
        due.extend(reversed(pending))
    return due


class SprintCloseRunner:
    """Adapts ``SprintService.close_current_sprint`` to the ``SprintCloser`` protocol."""

    def __init__(self, *, sprint_service: SprintService, uow: UnitOfWork) -> None:
        self._sprint_service = sprint_service
        self._uow = uow

    async def close_due_sprint(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
        correlation_id: str,
    ) -> ClosedSprint | None:
        try:
            sprint_run = await self._sprint_service.close_current_sprint(
                group_id=group_id,
                period_start=period_start,
                period_end=period_end,
            )
        except BusinessRuleViolation:
            logger.info(
                "sprint_close.duplicate_skipped group_id=%s period=%s..%s correlation_id=%s",
                group_id,
                period_start.isoformat(),
                period_end.isoformat(),
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
