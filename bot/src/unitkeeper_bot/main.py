from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from unitkeeper_bot.application.notifications import NotificationWorker
from unitkeeper_bot.application.start import StartService
from unitkeeper_bot.backend.client import BackendClient
from unitkeeper_bot.config import Settings
from unitkeeper_bot.handlers.common import build_common_router
from unitkeeper_bot.handlers.notifications import build_notification_router


async def run(settings: Settings) -> None:
    backend = BackendClient(
        base_url=str(settings.backend_base_url),
        internal_secret=settings.internal_bot_secret.get_secret_value(),
        timeout_seconds=settings.request_timeout_seconds,
    )
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(
        build_common_router(
            start_service=StartService(backend=backend),
            miniapp_url=str(settings.miniapp_url),
        )
    )
    dispatcher.include_router(build_notification_router(backend=backend))
    worker = NotificationWorker(backend=backend, bot=bot, miniapp_url=str(settings.miniapp_url))

    async def deliver_notifications() -> None:
        while True:
            await worker.deliver_ready()
            await asyncio.sleep(10)

    notification_task = asyncio.create_task(deliver_notifications())
    try:
        await dispatcher.start_polling(bot)
    finally:
        notification_task.cancel()
        await asyncio.gather(notification_task, return_exceptions=True)
        await backend.close()
        await bot.session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(Settings()))  # type: ignore[call-arg]


if __name__ == "__main__":
    main()
