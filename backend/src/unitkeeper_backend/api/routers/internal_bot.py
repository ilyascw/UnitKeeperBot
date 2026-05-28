from __future__ import annotations

from fastapi import APIRouter, Depends

from dishka.integrations.fastapi import DishkaRoute, FromDishka

from unitkeeper_backend.api.dependencies.internal import require_internal_auth
from unitkeeper_backend.api.schemas.bot import BotApproveRequest, BotRejectRequest, EnsureUserRequest
from unitkeeper_backend.api.schemas.common import CurrentContextResponse, TaskLogResponse, UserResponse
from unitkeeper_backend.application.bot.service import BotService
from unitkeeper_backend.application.models import TelegramIdentity

router = APIRouter(
    prefix="/internal/bot",
    tags=["internal-bot"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_internal_auth)],
)


@router.post("/users/ensure", response_model=UserResponse)
async def ensure_user(
    request: EnsureUserRequest,
    bot_service: FromDishka[BotService] = None,
) -> UserResponse:
    identity = TelegramIdentity(
        user_id=request.telegram_user_id,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        language_code=request.language_code,
        is_bot=request.is_bot,
    )
    user = await bot_service.ensure_user(identity)
    return UserResponse.model_validate(user, from_attributes=True)


@router.get("/users/{telegram_user_id}/context", response_model=CurrentContextResponse)
async def get_user_context(
    telegram_user_id: int,
    bot_service: FromDishka[BotService] = None,
) -> CurrentContextResponse:
    context = await bot_service.get_context(telegram_user_id)
    return CurrentContextResponse.model_validate(context, from_attributes=True)


@router.post("/task-logs/{log_id}/approve", response_model=TaskLogResponse)
async def approve_task_log(
    log_id: int,
    request: BotApproveRequest,
    bot_service: FromDishka[BotService] = None,
) -> TaskLogResponse:
    log = await bot_service.approve(telegram_user_id=request.telegram_user_id, log_id=log_id)
    return TaskLogResponse.model_validate(log, from_attributes=True)


@router.post("/task-logs/{log_id}/reject", response_model=TaskLogResponse)
async def reject_task_log(
    log_id: int,
    request: BotRejectRequest,
    bot_service: FromDishka[BotService] = None,
) -> TaskLogResponse:
    log = await bot_service.reject(
        telegram_user_id=request.telegram_user_id,
        log_id=log_id,
        reason=request.reason,
    )
    return TaskLogResponse.model_validate(log, from_attributes=True)
