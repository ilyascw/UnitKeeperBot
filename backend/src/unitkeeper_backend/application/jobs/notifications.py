"""Notification producers used by scheduler jobs, independent from bot delivery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class EventPublisher(Protocol):
    async def enqueue_once(
        self,
        *,
        event_type: str,
        recipient_user_id: int,
        group_id: int,
        payload: dict[str, object],
        deep_link_path: str,
        dedupe_key: str,
        correlation_id: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class SprintMemberReport:
    user_id: int
    planned_units: str
    completed_units: str
    balance_delta: str


class SprintReportPublisher:
    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher

    async def publish(
        self,
        *,
        group_id: int,
        group_name: str,
        owner_user_id: int,
        period: str,
        planned_units: str,
        completed_units: str,
        reports: list[SprintMemberReport],
        correlation_id: str,
    ) -> None:
        for report in reports:
            await self._publisher.enqueue_once(
                event_type="sprint_closed",
                recipient_user_id=report.user_id,
                group_id=group_id,
                payload={
                    "kind": "sprint_personal_report",
                    "period": period,
                    "planned_units": report.planned_units,
                    "completed_units": report.completed_units,
                    "balance_delta": report.balance_delta,
                },
                deep_link_path="/progress",
                dedupe_key=f"sprint-report:{group_id}:{period}:{report.user_id}",
                correlation_id=correlation_id,
            )
        await self._publisher.enqueue_once(
            event_type="sprint_closed",
            recipient_user_id=owner_user_id,
            group_id=group_id,
            payload={
                "kind": "sprint_owner_summary",
                "group_name": group_name,
                "period": period,
                "planned_units": planned_units,
                "completed_units": completed_units,
            },
            deep_link_path="/progress",
            dedupe_key=f"sprint-owner-summary:{group_id}:{period}",
            correlation_id=correlation_id,
        )


class ReminderPublisher:
    def __init__(self, publisher: EventPublisher) -> None:
        self._publisher = publisher

    async def pending_approvals(
        self, *, group_id: int, owner_user_id: int, count: int, period: str, correlation_id: str
    ) -> None:
        if count == 0:
            return
        await self._publisher.enqueue_once(
            event_type="reminder",
            recipient_user_id=owner_user_id,
            group_id=group_id,
            payload={"kind": "pending_approval_reminder", "count": count},
            deep_link_path="/tasks/history",
            dedupe_key=f"pending-approvals:{group_id}:{period}",
            correlation_id=correlation_id,
        )

    async def sprint_deadline(
        self, *, group_id: int, user_ids: list[int], deadline: str, period: str, correlation_id: str
    ) -> None:
        for user_id in user_ids:
            await self._publisher.enqueue_once(
                event_type="reminder",
                recipient_user_id=user_id,
                group_id=group_id,
                payload={"kind": "sprint_deadline_reminder", "deadline": deadline},
                deep_link_path="/tasks",
                dedupe_key=f"sprint-deadline:{group_id}:{period}:{user_id}",
                correlation_id=correlation_id,
            )
