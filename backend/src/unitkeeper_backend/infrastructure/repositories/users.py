from __future__ import annotations

from collections.abc import Sequence

from db.models import User
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from unitkeeper_backend.application.models import TelegramIdentity, UserProfile
from unitkeeper_backend.infrastructure.repositories.mappers import map_user


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> UserProfile | None:
        model = await self._session.get(User, user_id)
        return map_user(model) if model is not None else None

    async def list_by_ids(self, user_ids: Sequence[int]) -> list[UserProfile]:
        if not user_ids:
            return []
        query = select(User).where(User.id.in_(tuple(user_ids)))
        result = await self._session.execute(query)
        return [map_user(model) for model in result.scalars().all()]

    async def upsert_from_telegram(self, identity: TelegramIdentity) -> UserProfile:
        # A single atomic INSERT .. ON CONFLICT DO UPDATE, not a check-then-write:
        # two concurrent first-logins for the same new user (e.g. a double-fired
        # auth request) would otherwise race a plain get-then-insert into a
        # unique-constraint violation.
        values = {
            "id": identity.user_id,
            "username": identity.username,
            "first_name": identity.first_name,
            "last_name": identity.last_name,
            "language_code": identity.language_code,
            "is_bot": identity.is_bot,
        }
        insert_stmt = insert(User).values(**values)
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[User.id],
            set_={
                "username": insert_stmt.excluded.username,
                "first_name": insert_stmt.excluded.first_name,
                "last_name": insert_stmt.excluded.last_name,
                "language_code": insert_stmt.excluded.language_code,
                "is_bot": insert_stmt.excluded.is_bot,
            },
        ).returning(User)
        result = await self._session.execute(upsert_stmt)
        model = result.scalar_one()
        await self._session.flush()
        return map_user(model)
