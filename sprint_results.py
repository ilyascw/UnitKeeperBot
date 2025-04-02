import asyncio
from datetime import datetime, timedelta
from aiogram import Bot
from sqlalchemy import select
from db.models import Task, Log, Group, User, Balance
from db.database import async_session
import calendar

def get_sprint_end_date(start_day: str, duration: int):
    """Определяет дату окончания спринта, исходя из стартового дня и продолжительности"""
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
    
    # Определяем стартовый день в прошлом или сегодня
    days_back = (today.weekday() - weekday_index) % 7
    start_date = today - timedelta(days=days_back)

    # Дата окончания спринта
    end_date = start_date + timedelta(days=duration-1) ####поменять
    return end_date.date()

async def calculate_results(bot: Bot):
    try:
        now = datetime.now()

        

        async with async_session() as session:
            # Получаем все группы
            groups = await session.execute(select(Group))
            groups = groups.scalars().all()

            print(list(groups))
            for group in groups:
                start_day, duration, owner_id, weights = group.start_day, group.sprint_duration, group.owner_id, group.weights

                # Определяем дату окончания спринта
                end_date = get_sprint_end_date(start_day, duration-1)

                print(end_date)
                # Проверяем, соответствует ли текущая дата дате окончания спринта
                if now.date() != end_date:
                    continue  

                weekdays_dict = {
                    "понедельник": "Monday",
                    "вторник": "Tuesday",
                    "среда": "Wednesday",
                    "четверг": "Thursday",
                    "пятница": "Friday",
                    "суббота": "Saturday",
                    "воскресенье": "Sunday"
                }
                weekday_index = list(calendar.day_name).index(weekdays_dict[start_day])
                today = now
                days_back = (today.weekday() - weekday_index) % 7
                start_date = today - timedelta(days=days_back)

                user_results = {}
                total_plan = 0
                total_fact = 0

                # Получаем задачи группы
                tasks = await session.execute(select(Task).where(Task.group_id == group.id))
                tasks = tasks.scalars().all()

                # Получаем логи группы
                logs = await session.execute(select(Log).where(Log.group_id == group.id and Log.timestamp <= get_sprint_end_date(start_date, duration) and Log.timestamp >= start_date))
                logs = logs.scalars().all()

                # Получаем всех пользователей группы
                users = await session.execute(select(User).where(User.group_id == group.id))
                users = users.scalars().all()

                for user in users:
                    user_id = user.id
                    try:
                        user_chat = await bot.get_chat(user_id)
                        first_name = user_chat.first_name
                    except Exception as e:
                        first_name = "Неизвестный"

                    # Плановые юниты
                    plan_units = sum(float(task.cost) * int(task.frequency) for task in tasks) * (weights.get(str(user_id), 0))/100
                    # Фактические юниты
                    fact_units = sum(float(task.cost) for log in logs if log.user_id == user_id and log.status == "completed" 
                                     for task in tasks if task.id == log.task_id)

                    total_plan += plan_units
                    total_fact += fact_units

                    efficiency = (fact_units / plan_units) * 100 if plan_units else 0
                    user_results[user_id] = (first_name, plan_units, fact_units, efficiency)

                # 1. Начисление бонуса
                bonus = 0.25 * total_plan if total_fact >= total_plan else 0
                                # Обновляем баланс группы

                group_balance = await session.execute(
                    select(Group)
                    .where(Group.id == group.id)
                )

                group_balance = group_balance.scalar_one_or_none()

                if group_balance:
                    group_balance.balance = total_fact - total_plan

                await session.commit()

                # 2. Пересчет балансов пользователей
                for user_id in user_results.keys():
                    first_name, plan, fact, _ = user_results[user_id]
                    balance_change = (float(fact) - float(plan)) + bonus * weights.get(user_id, 0)

                    # Обновляем баланс пользователя
                    balance = await session.execute(
                        select(Balance)
                        .where(Balance.user_id == user_id, Balance.group_id == group.id)
                    )
                    balance = balance.scalar_one_or_none()

                    if balance:
                        balance.balance = round((float(balance.balance) + float(balance_change)), 2)
                    else:
                        balance = Balance(user_id=user_id, group_id=group.id, balance=balance_change)
                        session.add(balance)

                    await session.commit()

                # 3. Формирование и отправка отчета пользователям
                for user_id, (first_name, plan, fact, efficiency) in user_results.items():
                    text = (
                        f"📊 Итоги спринта:\n\n"
                        f"👤 {first_name}\n"
                        f"🔹 План: {plan} юнитов\n"
                        f"✅ Факт: {fact} юнитов\n"
                        f"📈 Эффективность: {efficiency:.1f}%\n"
                        f"💰 Новый баланс: {balance.balance:.2f} юнитов"
                    )
                    try:
                        await bot.send_message(user_id, text)

                    except Exception as e:
                        pass


                # 4. Отчет в общий чат
                summary_text = "📢 Итоги группы:\n\n" + f"Результат группы {bonus} ю.\n" + "\n".join([
                    f"👤 {first_name}: {fact}/{plan} юнитов ({eff:.1f}%)"
                    for user_id, (first_name, plan, fact, eff) in user_results.items()
                ])
                try:
                    await bot.send_message(owner_id, summary_text)
 
                except Exception as e:
                    pass

                # 5. Очистка логов группы (не требуется, так как логи хранятся в базе данных)


    except Exception as e:
        print(f'ошибка: {e}')

async def scheduler(bot: Bot):
    """Функция для запуска итогов по расписанию (23:59)"""

    while True:
        try:
            now = datetime.now()
            target_time = now.replace(hour=23, minute=59, second=0, microsecond=0)
            sleep_time = (target_time - now).total_seconds()

            if sleep_time < 0:
                sleep_time += 86400  # Если время прошло, ждем до следующего дня

            await asyncio.sleep(sleep_time)

            await calculate_results(bot)
        except Exception as e:
            print(f'ошибка {e}')

async def setup_sprint_scheduler(bot: Bot):
    """Запуск задачи подведения итогов"""
    asyncio.create_task(scheduler(bot))