"""Scheduler-facing orchestration for due sprint closes.

The runtime scheduler supplies due groups; this layer keeps close/retry decisions
and report-event production in backend application code, never in the bot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from unitkeeper_backend.application.jobs.notifications import SprintMemberReport, SprintReportPublisher


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
    async def close_due_sprint(self, *, group_id: int, correlation_id: str) -> ClosedSprint | None: ...


class SprintCloseJob:
    def __init__(self, *, closer: SprintCloser, reports: SprintReportPublisher) -> None:
        self._closer = closer
        self._reports = reports

    async def run(self, *, due_group_ids: list[int], correlation_id: str) -> int:
        closed_count = 0
        for group_id in due_group_ids:
            closed = await self._closer.close_due_sprint(group_id=group_id, correlation_id=correlation_id)
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
