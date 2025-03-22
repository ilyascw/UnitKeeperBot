from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Task, User, Log, Group
from db.database import async_session

router = Router()

class RejectionReason(StatesGroup):
    waiting_for_reason = State()

@router.message(Command("tasks"))
async def show_tasks(message: Message):
    """Выводит список задач группы с информацией о количестве оставшихся выполнений в кнопках."""
    user_id = message.from_user.id

    async with async_session() as session:
        # Проверяем, состоит ли пользователь в группе
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await message.answer("❌ Ты не состоишь в группе.")
            return

        group_id = user.group_id

        # Получаем все задачи группы
        tasks = await session.execute(select(Task).where(Task.group_id == group_id, Task.status == True))
        tasks = tasks.scalars().all()

        if not tasks:
            await message.answer("📭 В группе пока нет задач.")
            return

        # Фильтруем логи за текущую неделю
        current_time = datetime.now()
        week_start = datetime(current_time.year, current_time.month, current_time.day) - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=6)

        remaining_tasks = []

        # Проходим по всем задачам группы
        for task in tasks:
            # Получаем количество выполненных задач за текущую неделю
            completed_count = await session.execute(
                select(Log)
                .where(
                    Log.task_id == task.id,
                    Log.status == "completed",
                    Log.timestamp >= week_start,
                    Log.timestamp <= week_end
                )
            )
            completed_count = len(completed_count.scalars().all())

            # Если выполнено меньше, чем требуется, добавляем в список оставшихся
            if completed_count < task.frequency:
                remaining_tasks.append((task.id, task.title, task.cost, task.frequency - completed_count))

        if remaining_tasks:
            # Создаем клавиатуру с кнопками для выбора задачи
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"{title} - {cost} юнитов", callback_data=f"task_{task_id}_{remaining}")]
                    for task_id, title, cost, remaining in remaining_tasks
                ]
            )

            await message.answer("📋 Список задач:", reply_markup=keyboard)
        else:
            await message.answer("✅ Все задачи выполнены на этой неделе!")

@router.callback_query(lambda c: c.data.startswith("task_"))
async def select_task(callback: CallbackQuery):
    """Пользователь выбирает задачу. Появляются кнопки 'Сделано' и 'Отказаться'."""
    task_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await callback.answer("❌ Ты не состоишь в группе.", show_alert=True)
            return

        task = await session.execute(select(Task).where(Task.id == task_id, Task.group_id == user.group_id))
        task = task.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сделано", callback_data=f"done_{task_id}")],
            [InlineKeyboardButton(text="❌ Отказаться", callback_data=f"cancel_{task_id}")]
        ])

        await callback.message.edit_text(
                        f"Задача: {task.title}\nСтоимость: {task.cost} юнитов\nОсталось: {int(callback.data.split('_')[2])}",
                        reply_markup=keyboard
            )

@router.callback_query(lambda c: c.data.startswith("cancel_"))
async def cancel_task(callback: CallbackQuery):
    """Пользователь отказывается от выполнения задачи и возвращается к выбору."""
    user_id = callback.from_user.id

    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await callback.message.edit_text("❌ Ты не состоишь в группе.")
            return

        group_id = user.group_id

        # Получаем все задачи группы
        tasks = await session.execute(select(Task).where(Task.group_id == group_id, Task.status == True))
        tasks = tasks.scalars().all()

        if not tasks:
            await callback.message.edit_text("📭 В группе пока нет задач.")
            return

        # Фильтруем логи за текущую неделю
        current_time = datetime.now()
        week_start = datetime(current_time.year, current_time.month, current_time.day) - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=6)

        remaining_tasks = []

        # Проходим по всем задачам группы
        for task in tasks:
            # Получаем количество выполненных задач за текущую неделю
            completed_count = await session.execute(
                select(Log)
                .where(
                    Log.task_id == task.id,
                    Log.status == "completed",
                    Log.timestamp >= week_start,
                    Log.timestamp <= week_end
                )
            )
            completed_count = len(completed_count.scalars().all())

            # Если выполнено меньше, чем требуется, добавляем в список оставшихся
            if completed_count < task.frequency:
                remaining_tasks.append((task.id, task.title, task.cost, task.frequency - completed_count))

        if remaining_tasks:
            # Создаем клавиатуру с кнопками для выбора задачи
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"{title} - {cost} юнитов", callback_data=f"task_{task_id}_{remaining}")]
                    for task_id, title, cost, remaining in remaining_tasks
                ]
            )

            await callback.message.edit_text("📋 Список задач:", reply_markup=keyboard)
        else:
            await callback.message.edit_text("✅ Все задачи выполнены на этой неделе!")

@router.callback_query(lambda c: c.data.startswith("done_"))
async def confirm_task(callback: CallbackQuery, bot: Bot):
    """Пользователь отмечает задачу как выполненную. Если в группе только 1 участник — автоматически подтверждаем выполнение."""
    task_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        # Получаем пользователя
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await callback.answer("❌ Ты не состоишь в группе.", show_alert=True)
            return

        group_id = user.group_id

        # Получаем задачу
        task = await session.execute(select(Task).where(Task.id == task_id, Task.group_id == group_id))
        task = task.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        # Получаем всех участников группы
        group_members = await session.execute(select(User).where(User.group_id == group_id))
        group_members = group_members.scalars().all()

        # Если в группе только один участник, сразу подтверждаем задачу как выполненную
        if len(group_members) == 1:
            log = Log(
                group_id=group_id,
                user_id=user_id,
                task_id=task_id,
                status="completed",
                timestamp=datetime.now()
            )
            session.add(log)
            await session.commit()

            await callback.message.edit_text(f"✅ Задача '{task.title}' выполнена!")
            return

        # Добавляем задачу в логи с состоянием "ожидает подтверждения"
        log = Log(
            group_id=group_id,
            user_id=user_id,
            task_id=task_id,
            status="pending",
            timestamp=datetime.now()
        )
        session.add(log)
        await session.commit()

        # Получаем ID созданного лога
        log_id = log.id

        # Кнопки подтверждения и отказа
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{task_id}_{log_id}")],
            [InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{task_id}_{log_id}")]
        ])

        # Уведомляем остальных участников группы
        for member in group_members:
            if member.id != user_id:
                await bot.send_message(
                    member.id,
                    f"📋 Пользователь {callback.from_user.first_name} отметил задачу '{task.title}' как выполненную. Ожидается ваше подтверждение.",
                    reply_markup=keyboard
                )

        await callback.message.edit_text(f"⏳ Задача '{task.title}' отмечена как выполненная. Ожидание подтверждения...")

@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_execution(callback: CallbackQuery, bot: Bot):
    """Другие участники подтверждают выполнение задачи."""
    from .temp_results import get_sprint_start_date

    task_id = int(callback.data.split("_")[1])
    log_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    async with async_session() as session:
        # Получаем пользователя
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await callback.answer("❌ Ты не состоишь в группе.", show_alert=True)
            return

        group_id = user.group_id

        # Получаем задачу
        task = await session.execute(select(Task).where(Task.id == task_id, Task.group_id == group_id))
        task = task.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        task_title = task.title

        # Находим лог по log_id
        log = await session.execute(
            select(Log)
            .where(
                Log.id == log_id,
                Log.task_id == task_id,
                Log.status == "pending",
                Log.group_id == group_id
            )
        )

        group = await session.execute(
            select(Group)
            .where(
                Group.id == group_id
            )
        )
        group = group.scalar_one_or_none()
        log = log.scalar_one_or_none()

        if not log:
            await callback.answer("❌ Задача не найдена или уже подтверждена.", show_alert=True)
            return

        # Проверяем, сколько раз задача уже была выполнена за текущий спринт
        sprint_start = get_sprint_start_date(group.start_day)
        sprint_end = sprint_start + timedelta(days=group.sprint_duration)

        completed_count = await session.execute(
            select(func.count(Log.id))
            .where(
                Log.task_id == task_id,
                Log.status == "completed",
                Log.timestamp >= sprint_start,
                Log.timestamp <= sprint_end
            )
        )
        completed_count = completed_count.scalar()

        # Если лимит выполнений исчерпан, отменяем подтверждение
        if completed_count >= task.frequency:
            await callback.answer("❌ Лимит выполнений задачи исчерпан.", show_alert=True)
            await callback.message.edit_text(f"❌ Лимит выполнений задачи исчерпан.")
            await bot.send_message(
            log.user_id,
            f"❌ Лимит выполнений '{task_title}' исчерпан."
            )
            return

        # Обновляем лог на "выполнено"
        log.status = "completed"
        log.timestamp = datetime.now()
        await session.commit()

        await callback.message.edit_text(f"✅ Задача '{task_title}' подтверждена как выполненная.")

        # Уведомляем пользователя, который выполнял задачу
        await bot.send_message(
            log.user_id,
            f"✅ Ваша задача '{task_title}' была подтверждена как выполненная."
        )

        await callback.answer()

@router.callback_query(lambda c: c.data.startswith("reject_"))
async def reject_execution(callback: CallbackQuery, state: FSMContext):
    """Запрос причины отказа от подтверждения задачи."""
    _, task_id, task_owner_id = callback.data.split("_")
    task_id, task_owner_id = int(task_id), int(task_owner_id)

    await state.update_data(task_id=task_id, task_owner_id=task_owner_id)
    await state.set_state(RejectionReason.waiting_for_reason)

    await callback.message.answer("❌ Укажите причину отказа:")
    await callback.answer()

@router.message(RejectionReason.waiting_for_reason)
async def process_rejection_reason(message: Message, state: FSMContext, bot: Bot):
    """Обрабатываем введенную причину отказа."""

    data = await state.get_data()
    task_id = data["task_id"]
    task_owner_id = data["task_owner_id"]
    reason = message.text
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()
        task = await session.execute(select(Task).where(Task.id == task_id, Task.group_id == user.group_id, ))
        task = task.scalar_one_or_none()

        if user is None or user.group_id is None:
            await message.answer("❌ Ты не состоишь в группе.", show_alert=True)
            return
        
        task = await session.execute(select(Task).where(Task.id == task_id, Task.group_id == user.group_id, ))
        task = task.scalar_one_or_none()
        task_title = task.title
        await session.commit()

        log = await session.execute(
            select(Log)
            .where(
                Log.id == task_owner_id,
            )
        )
        log = log.scalar_one_or_none()

        # Отправляем причину отказа пользователю, который выполнял задачу
        await bot.send_message(
            log.user_id,
            f"❌ Ваша задача '{task_title}' не была подтверждена.\nПричина отказа: {reason}"
        )

    await message.answer("✅ Ваш отказ был зарегистрирован.")
    await state.clear()

@router.message(Command("list_of_tasks"))
async def list_of_tasks(message: Message):
    """Команда /list_of_tasks для вывода всех задач, связанных с группой."""
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await message.answer("❌ Вы не состоите в группе.")
            return

        group_id = user.group_id

        # Получаем все задачи группы
        tasks = await session.execute(select(Task).where(Task.group_id == group_id, Task.status == True))
        tasks = tasks.scalars().all()

        if not tasks:
            await message.answer("❌ Для вашей группы нет задач.")
            return

        # Создаем клавиатуру с кнопками для выбора задачи
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{task.title}", callback_data=f"detail_{task.id}")]
                for task in tasks
            ]
        )

        await message.answer("📋 Список задач:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("detail_"))
async def task_detail(callback: CallbackQuery):
    """Показывает подробную информацию о задаче с кнопкой 'Назад'."""
    task_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await callback.answer("❌ Вы не состоите в группе.", show_alert=True)
            return

        group_id = user.group_id

        # Получаем задачу по ID
        task = await session.execute(select(Task).where(Task.id == task_id, Task.group_id == group_id))
        task = task.scalar_one_or_none()
        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        # Фильтруем логи за текущую неделю
        current_time = datetime.now()
        week_start = datetime(current_time.year, current_time.month, current_time.day) - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=group.duration)

        # Получаем количество выполненных задач за текущую неделю
        completed_count = await session.execute(
            select(Log)
            .where(
                Log.task_id == task.id,
                Log.status == "completed",
                Log.timestamp >= week_start,
                Log.timestamp <= week_end
            )
        )
        completed_count = len(completed_count.scalars().all())

        # Вычисляем оставшиеся задачи на спринт
        remaining_tasks = task.frequency - completed_count

        # Формируем сообщение с подробной информацией о задаче
        response = (
            f"🔹 Задача ID: {task.id}\n"
            f"Название: {task.title}\n"
            f"Частота выполнения: {task.frequency}\n"
            f"Стоимость: {task.cost} ю\n"
            f"Осталось выполнить: {remaining_tasks} раз(а) на текущий спринт\n"
        )

        # Кнопка "Назад"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_task_list")]
            ]
        )

        await callback.message.edit_text(response, reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "back_to_task_list")
async def back_to_task_list(callback: CallbackQuery):
    """Возвращает пользователя к списку задач."""
    user_id = callback.from_user.id

    async with async_session() as session:
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await callback.answer("❌ Вы не состоите в группе.", show_alert=True)
            return

        group_id = user.group_id

        # Получаем все задачи группы
        tasks = await session.execute(select(Task).where(Task.group_id == group_id, Task.status == True))
        tasks = tasks.scalars().all()

        if not tasks:
            await callback.message.edit_text("❌ Для вашей группы нет задач.")
            return

        # Создаем клавиатуру с кнопками для выбора задачи
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{task.title}", callback_data=f"detail_{task.id}")]
                for task in tasks
            ]
        )

        await callback.message.edit_text("📋 Список задач:", reply_markup=keyboard)