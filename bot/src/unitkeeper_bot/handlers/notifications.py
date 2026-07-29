from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from unitkeeper_bot.backend.client import BackendGateway, BackendTransportError


def build_notification_router(*, backend: BackendGateway) -> Router:
    router = Router(name="notifications")

    @router.callback_query(F.data.startswith("approval:"))
    async def approval_callback(callback: CallbackQuery) -> None:
        if callback.data is None:
            return
        _, raw_log_id, action = callback.data.split(":", maxsplit=2)
        if not raw_log_id.isdigit() or action not in {"approve", "reject"}:
            await callback.answer("Некорректное действие", show_alert=True)
            return
        try:
            if action == "approve":
                await backend.approve_task_log(
                    log_id=int(raw_log_id), telegram_user_id=callback.from_user.id
                )
                result = "Отметка подтверждена"
            else:
                await backend.reject_task_log(
                    log_id=int(raw_log_id),
                    telegram_user_id=callback.from_user.id,
                    reason="Отклонено через Telegram",
                )
                result = "Отметка отклонена"
        except BackendTransportError:
            await callback.answer("Не удалось выполнить действие", show_alert=True)
            return
        await callback.answer(result)
        if isinstance(callback.message, Message):
            await callback.message.edit_reply_markup(reply_markup=None)

    return router
