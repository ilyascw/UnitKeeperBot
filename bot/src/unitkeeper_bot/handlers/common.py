from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo

from unitkeeper_bot.application.start import StartService
from unitkeeper_bot.backend.client import BackendTransportError, TelegramUser

_logger = logging.getLogger(__name__)


def build_common_router(*, start_service: StartService, miniapp_url: str) -> Router:
    bound_router = Router(name="common")

    @bound_router.message(CommandStart())
    async def start(message: Message) -> None:
        if message.from_user is None:
            return
        user = TelegramUser(
            id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
            is_bot=message.from_user.is_bot,
        )
        try:
            context = await start_service.initialize_user(user)
        except BackendTransportError:
            _logger.exception("Unable to initialize Telegram user", extra={"telegram_user_id": user.id})
            await message.answer("UnitKeeper временно недоступен. Попробуйте ещё раз позже.")
            return

        text = "Откройте UnitKeeper, чтобы продолжить работу с группой."
        if not context.has_active_group:
            text = "Откройте UnitKeeper, чтобы создать группу или присоединиться к существующей."
        await message.answer(text, reply_markup=_miniapp_keyboard(miniapp_url))

    @bound_router.message(Command("help"))
    async def help_command(message: Message) -> None:
        await message.answer("Основные действия доступны в приложении UnitKeeper.", reply_markup=_miniapp_keyboard(miniapp_url))

    @bound_router.message(Command("about"))
    async def about(message: Message) -> None:
        await message.answer(
            "UnitKeeper помогает группе планировать бытовые задачи и учитывать вклад участников.",
            reply_markup=_miniapp_keyboard(miniapp_url),
        )

    @bound_router.message(F.text.startswith("/"))
    async def legacy_command(message: Message) -> None:
        await message.answer("Эта команда переехала в приложение UnitKeeper.", reply_markup=_miniapp_keyboard(miniapp_url))

    @bound_router.message()
    async def fallback(message: Message) -> None:
        await message.answer("Откройте UnitKeeper для работы с задачами и группой.", reply_markup=_miniapp_keyboard(miniapp_url))

    return bound_router


def _miniapp_keyboard(miniapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть UnitKeeper", web_app=WebAppInfo(url=miniapp_url))]],
    )
