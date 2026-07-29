"""Scheduler process entrypoint: runs the sprint-close job on a recurring interval.

Runs as a separate long-lived process from the FastAPI app (see
`backend/Dockerfile` / root `docker-compose.yml` for how to wire a second
container using the same image with `CMD ["python", "-m",
"unitkeeper_backend.entrypoints.scheduler"]`).

Timezone policy: the job is scheduled with an explicit UTC trigger, matching
`UtcClock` and the domain sprint-window math (`domain/services/sprint_math.py`),
which both anchor to UTC. Every group's sprint window is currently evaluated
in UTC regardless of its own `timezone` field; group-local scheduling is not
implemented yet.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from db.enums import NotificationEventType
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from unitkeeper_backend.application.jobs.notifications import SprintReportPublisher
from unitkeeper_backend.application.jobs.scheduler import SprintCloseJob
from unitkeeper_backend.application.jobs.sprint_close import SprintCloseRunner, list_due_group_ids
from unitkeeper_backend.application.sprints.service import SprintService
from unitkeeper_backend.config import Settings, settings
from unitkeeper_backend.infrastructure.db.session import build_engine, build_session_maker
from unitkeeper_backend.infrastructure.repositories.notifications import (
    SqlAlchemyNotificationRepository,
)
from unitkeeper_backend.infrastructure.time import UtcClock
from unitkeeper_backend.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


class _OutboxEventPublisher:
    """Adapts SqlAlchemyNotificationRepository.enqueue_once to the EventPublisher protocol."""

    def __init__(self, repository: SqlAlchemyNotificationRepository) -> None:
        self._repository = repository

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
    ) -> None:
        await self._repository.enqueue_once(
            dedupe_key=dedupe_key,
            correlation_id=correlation_id,
            event_type=NotificationEventType(event_type),
            recipient_user_id=recipient_user_id,
            group_id=group_id,
            payload=payload,
            deep_link_path=deep_link_path,
        )


# Runs once a day, shortly after UTC midnight, so a group whose sprint window
# ended "yesterday" (period_end == yesterday's date) is picked up as soon as
# today begins. See `list_due_group_ids` for the exact due-ness check.
SPRINT_CLOSE_CRON = CronTrigger(hour=0, minute=5, timezone=timezone.utc)


async def run_sprint_close_once(session_maker: async_sessionmaker[AsyncSession]) -> int:
    """Run one sprint-close pass. Safe to call repeatedly (duplicate-close protected)."""
    clock = UtcClock()
    correlation_id = f"sprint-close-{uuid.uuid4()}"
    async with session_maker() as session:
        uow = SqlAlchemyUnitOfWork(session)
        sprint_service = SprintService(uow=uow, clock=clock)
        closer = SprintCloseRunner(sprint_service=sprint_service, uow=uow)
        reports = SprintReportPublisher(
            _OutboxEventPublisher(SqlAlchemyNotificationRepository(session))
        )
        job = SprintCloseJob(closer=closer, reports=reports)

        due_group_ids = await list_due_group_ids(uow=uow, clock=clock)
        logger.info(
            "sprint_close.run_start due_count=%s correlation_id=%s",
            len(due_group_ids),
            correlation_id,
        )
        closed_count = await job.run(due_group_ids=due_group_ids, correlation_id=correlation_id)
        await session.commit()
        logger.info(
            "sprint_close.run_finished closed_count=%s correlation_id=%s",
            closed_count,
            correlation_id,
        )
        return closed_count


def build_scheduler(app_settings: Settings, engine: AsyncEngine) -> AsyncIOScheduler:
    session_maker = build_session_maker(engine)
    scheduler = AsyncIOScheduler(timezone=timezone.utc)
    scheduler.add_job(
        run_sprint_close_once,
        trigger=SPRINT_CLOSE_CRON,
        args=[session_maker],
        id="sprint_close",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    return scheduler


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    engine = build_engine(settings)
    scheduler = build_scheduler(settings, engine)
    scheduler.start()
    logger.info("sprint_close.scheduler_started")
    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
