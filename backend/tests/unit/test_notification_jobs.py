from __future__ import annotations

import pytest

from unitkeeper_backend.application.jobs.notifications import (
    ReminderPublisher,
    SprintMemberReport,
    SprintReportPublisher,
)
from unitkeeper_backend.application.jobs.scheduler import ClosedSprint, SprintCloseJob


class FakePublisher:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.keys: set[str] = set()

    async def enqueue_once(self, **kwargs: object) -> None:
        key = str(kwargs["dedupe_key"])
        if key not in self.keys:
            self.keys.add(key)
            self.calls.append(kwargs)


@pytest.mark.asyncio
async def test_sprint_reports_are_durable_deduplicated_and_correlated() -> None:
    publisher = FakePublisher()
    job = SprintReportPublisher(publisher)
    reports = [SprintMemberReport(1, "5", "6", "+1"), SprintMemberReport(2, "5", "6", "+1")]

    for _ in range(2):
        await job.publish(
            group_id=7,
            group_name="Home",
            owner_user_id=1,
            period="2026-07-06..2026-07-12",
            planned_units="10",
            completed_units="12",
            reports=reports,
            correlation_id="close-7",
        )

    assert len(publisher.calls) == 3
    assert {item["correlation_id"] for item in publisher.calls} == {"close-7"}


@pytest.mark.asyncio
async def test_reminders_skip_empty_queue_and_are_idempotent() -> None:
    publisher = FakePublisher()
    job = ReminderPublisher(publisher)

    await job.pending_approvals(
        group_id=7, owner_user_id=1, count=0, period="2026-07-12", correlation_id="reminders-1"
    )
    await job.pending_approvals(
        group_id=7, owner_user_id=1, count=2, period="2026-07-12", correlation_id="reminders-1"
    )
    await job.pending_approvals(
        group_id=7, owner_user_id=1, count=2, period="2026-07-12", correlation_id="reminders-1"
    )
    await job.sprint_deadline(
        group_id=7,
        user_ids=[1, 2],
        deadline="today",
        period="2026-07-12",
        correlation_id="reminders-1",
    )

    assert len(publisher.calls) == 3
    assert all(item["correlation_id"] == "reminders-1" for item in publisher.calls)


@pytest.mark.asyncio
async def test_scheduler_does_not_publish_reports_for_already_closed_sprint() -> None:
    publisher = FakePublisher()

    class Closer:
        closed = False

        async def close_due_sprint(
            self, *, group_id: int, correlation_id: str
        ) -> ClosedSprint | None:
            if group_id == 7 and not self.closed:
                self.closed = True
                return ClosedSprint(
                    7,
                    "Home",
                    1,
                    "2026-07-06..2026-07-12",
                    "10",
                    "12",
                    [SprintMemberReport(1, "10", "12", "+2")],
                )
            return None

    result = await SprintCloseJob(closer=Closer(), reports=SprintReportPublisher(publisher)).run(
        due_group_ids=[7, 7], correlation_id="scheduler-7"
    )

    assert result == 1
    assert len(publisher.calls) == 2
