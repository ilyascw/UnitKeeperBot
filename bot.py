import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import routers
from sprint_results import setup_sprint_scheduler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем обработчики
for router in routers:
    dp.include_router(router)

async def main():
    """Основная асинхронная функция запуска бота"""
    
    # Запускаем подведение итогов по расписанию
    await setup_sprint_scheduler(bot)

    await dp.start_polling(bot)  # Запускаем бота

if __name__ == "__main__":
    asyncio.run(main())