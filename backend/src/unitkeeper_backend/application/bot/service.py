from __future__ import annotations

import logging

from unitkeeper_backend.application.context.service import CurrentContextService
from unitkeeper_backend.application.models import CurrentContext, TaskLogInfo, TelegramIdentity, UserProfile
from unitkeeper_backend.application.ports import UnitOfWork
from unitkeeper_backend.application.tasks.service import TaskService
from unitkeeper_backend.domain.errors import NotFoundError

_audit = logging.getLogger("unitkeeper.bot.audit")


class BotService:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        context_service: CurrentContextService,
        task_service: TaskService,
    ) -> None:
        self._uow = uow
        self._context_service = context_service
        self._task_service = task_service

    async def ensure_user(self, identity: TelegramIdentity) -> UserProfile:
        user = await self._uow.users.upsert_from_telegram(identity)
        await self._uow.commit()
        _audit.info(
            "bot.ensure_user",
            extra={"telegram_user_id": identity.user_id, "result": "ok"},
        )
        return user

    async def get_context(self, telegram_user_id: int) -> CurrentContext:
        context = await self._context_service.resolve(telegram_user_id)
        _audit.info(
            "bot.get_context",
            extra={
                "telegram_user_id": telegram_user_id,
                "group_id": context.group.id if context.group else None,
            },
        )
        return context

    async def approve(self, *, telegram_user_id: int, log_id: int) -> TaskLogInfo:
        group_id = await self._require_group_id(telegram_user_id)
        log = await self._task_service.approve(
            group_id=group_id,
            approver_user_id=telegram_user_id,
            log_id=log_id,
        )
        _audit.info(
            "bot.approve",
            extra={
                "telegram_user_id": telegram_user_id,
                "group_id": group_id,
                "task_log_id": log_id,
                "result": "ok",
            },
        )
        return log

    async def reject(self, *, telegram_user_id: int, log_id: int, reason: str) -> TaskLogInfo:
        group_id = await self._require_group_id(telegram_user_id)
        log = await self._task_service.reject(
            group_id=group_id,
            approver_user_id=telegram_user_id,
            log_id=log_id,
            rejection_reason=reason,
        )
        _audit.info(
            "bot.reject",
            extra={
                "telegram_user_id": telegram_user_id,
                "group_id": group_id,
                "task_log_id": log_id,
                "result": "ok",
            },
        )
        return log

    async def _require_group_id(self, telegram_user_id: int) -> int:
        context = await self._context_service.resolve(telegram_user_id)
        if context.group is None:
            raise NotFoundError("User has no active group")
        return context.group.id
