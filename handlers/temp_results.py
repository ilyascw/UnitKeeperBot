# Основные импорты aiogram
from aiogram import Router, F, Bot
from aiogram.types import (
    Message
)
from aiogram.filters import Command

# Импорты для работы с базой данных
from sqlalchemy import select
from db.database import async_session
from db.models import Group, User, Task, Log

# Импорты для работы с датами и временем
from datetime import datetime, timedelta
import calendar

router = Router()

def get_sprint_start_date(start_day: str):
    """Определяет дату начала текущего спринта."""
    weekdays_dict = {
            "понедельник": "Monday",
            "вторник": "Tuesday",
            "среда": "Wednesday",
            "четверг": "Thursday",
            "пятница": "Friday",
            "суббота": "Saturday",
            "воскресенье": "Sunday"
    }
    today = datetime.now()
    weekday_index = list(calendar.day_name).index(weekdays_dict[start_day])  # Индекс дня начала (0=Monday, 6=Sunday)
    
    # Определяем ближайший стартовый день в прошлом или сегодня
    days_back = (today.weekday() - weekday_index) % 7
    start_date = today - timedelta(days=days_back)
    return start_date.date()

@router.message(Command("temp_results"))
async def temp_results(message: Message):
    """Обработчик команды /temp_results. Выводит промежуточные итоги спринта."""
    user_id = message.from_user.id

    async with async_session() as session:
        # Получаем пользователя
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await message.answer("❌ Вы не состоите в группе.")
            return

        group_id = user.group_id

        # Получаем данные группы
        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()

        if group is None:
            await message.answer("❌ Группа не найдена.")
            return

        start_day, duration, weights = group.start_day, group.sprint_duration, group.weights

        # Определяем дату начала и окончания текущего спринта
        sprint_start = get_sprint_start_date(start_day)
        sprint_end = sprint_start + timedelta(days=duration - 1)

        # Получаем задачи группы
        tasks = await session.execute(select(Task).where(Task.group_id == group_id))
        tasks = tasks.scalars().all()

        # Получаем логи группы за текущий спринт
        logs = await session.execute(
            select(Log)
            .where(
                Log.group_id == group_id,
                Log.status == "completed",
                Log.timestamp >= sprint_start,
                Log.timestamp <= sprint_end
            )
        )
        logs = logs.scalars().all()

        # Подсчитываем фактические юниты
        fact_units = sum(task.cost for log in logs for task in tasks if task.id == log.task_id and log.user_id == message.from_user.id)

        # Подсчитываем плановые юниты
        plan_units = float(sum(task.cost * task.frequency for task in tasks)) * float(weights.get(str(user_id), 0)/100)

        # Подсчитываем выполненные задачи
        completed_tasks = {}
        for log in logs:
            task = next((task for task in tasks if task.id == log.task_id and log.user_id == message.from_user.id), None)
            if task:
                if task.title in completed_tasks:
                    completed_tasks[task.title] += 1
                else:
                    completed_tasks[task.title] = 1

        # Прогресс (в процентах)
        progress = (float(fact_units) / plan_units) * 100 if plan_units else 0

        # Формируем сообщение
        response = (
            f"Привет, информация по текущим результатам!\n\n"
            f"📅 Прошло дней: {(datetime.now().date() - sprint_start).days}\n"
            f"💰 Накоплено юнитов: {fact_units:.2f} / {plan_units:.2f}\n\n"
            f"✅ Выполненные задачи:\n"
        )

        # Добавляем выполненные задачи
        for task_title, count in completed_tasks.items():
            response += f"  • {task_title} — {count} раз(а)\n"

        # Добавляем прогресс-бар
        progress_bar = "🟩" * int(progress // 10) + "⬜️" * (10 - int(progress // 10))
        response += f"\n📊 Прогресс: {progress:.1f}%\n{progress_bar}"

        # Отправляем сообщение
        await message.answer(response)