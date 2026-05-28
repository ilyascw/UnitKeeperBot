from __future__ import annotations

from unitkeeper_backend.application.models import CurrentContext
from unitkeeper_backend.application.ports import UnitOfWork
from unitkeeper_backend.domain.errors import AuthenticationError


class CurrentContextService:
    def __init__(self, *, uow: UnitOfWork) -> None:
        self._uow = uow

    async def resolve(self, user_id: int) -> CurrentContext:
        user = await self._uow.users.get_by_id(user_id)
        if user is None:
            raise AuthenticationError("Authenticated user is not registered")

        membership = await self._uow.groups.get_active_membership(user_id)
        group = None
        if membership is not None:
            group = await self._uow.groups.get_by_id(membership.group_id)
        return CurrentContext(user=user, membership=membership, group=group)
