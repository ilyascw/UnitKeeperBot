from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from unitkeeper_backend.infrastructure.repositories.groups import SqlAlchemyGroupRepository
from unitkeeper_backend.infrastructure.repositories.sprints import SqlAlchemySprintRepository
from unitkeeper_backend.infrastructure.repositories.tasks import SqlAlchemyTaskRepository
from unitkeeper_backend.infrastructure.repositories.users import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = SqlAlchemyUserRepository(session)
        self.groups = SqlAlchemyGroupRepository(session)
        self.tasks = SqlAlchemyTaskRepository(session)
        self.sprints = SqlAlchemySprintRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
