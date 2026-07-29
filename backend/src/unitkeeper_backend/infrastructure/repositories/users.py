from __future__ import annotations

from collections.abc import Sequence

from db.models import User
from sqlalchemy import select
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
        model = await self._session.get(User, identity.user_id)
        if model is None:
            model = User(
                id=identity.user_id,
                username=identity.username,
                first_name=identity.first_name,
                last_name=identity.last_name,
                language_code=identity.language_code,
                is_bot=identity.is_bot,
            )
            self._session.add(model)
            await self._session.flush()
            return map_user(model)

        model.username = identity.username
        model.first_name = identity.first_name
        model.last_name = identity.last_name
        model.language_code = identity.language_code
        model.is_bot = identity.is_bot
        await self._session.flush()
        return map_user(model)
