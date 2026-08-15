"""Scheduler-facing orchestration for due sprint closes.

The runtime scheduler supplies due groups; this layer keeps close/retry decisions
and report-event production in backend application code, never in the bot.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from unitkeeper_backend.application.jobs.notifications import (
    SprintMemberReport,
    SprintReportPublisher,
)


@dataclass(frozen=True, slots=True)
class DueSprintWindow:
    """A specific window of a specific group that has ended and is unsettled.

    Discovery hands the exact period to the closer rather than a bare group id,
    so a catch-up pass settles the window it found instead of whichever one
    happens to be current by the time the close runs.
    """

    group_id: int
    period_start: date
    period_end: date


@dataclass(frozen=True, slots=True)
class ClosedSprint:
    group_id: int
    group_name: str
    owner_user_id: int
    period: str
    planned_units: str
    completed_units: str
    reports: list[SprintMemberReport]


class SprintCloser(Protocol):
    async def close_due_sprint(
        self,
        *,
        group_id: int,
        period_start: date,
        period_end: date,
        correlation_id: str,
    ) -> ClosedSprint | None: ...


class SprintCloseJob:
    def __init__(self, *, closer: SprintCloser, reports: SprintReportPublisher) -> None:
        self._closer = closer
        self._reports = reports

    async def run(self, *, due_windows: Sequence[DueSprintWindow], correlation_id: str) -> int:
        """Settle each due window in the order given (discovery yields oldest first)."""
        closed_count = 0
        for due in due_windows:
            closed = await self._closer.close_due_sprint(
                group_id=due.group_id,
                period_start=due.period_start,
                period_end=due.period_end,
                correlation_id=correlation_id,
            )
            if closed is None:
                continue
            await self._reports.publish(
                group_id=closed.group_id,
                group_name=closed.group_name,
                owner_user_id=closed.owner_user_id,
                period=closed.period,
                planned_units=closed.planned_units,
                completed_units=closed.completed_units,
                reports=closed.reports,
                correlation_id=correlation_id,
            )
            closed_count += 1
        return closed_count
