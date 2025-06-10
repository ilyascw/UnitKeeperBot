from aiogram import Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta
from sqlalchemy import select, func
from db.models import Task, User, Log, Group
from db.database import async_session
import random

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
        tasks = await session.execute(
            select(Task).where(Task.group_id == group_id, Task.status == True)
        )
        tasks = tasks.scalars().all()

        if not tasks:
            await message.answer("📭 В группе пока нет задач.")
            return

        # Фильтруем логи за текущую неделю
        current_time = datetime.now()
        week_start = datetime(
            current_time.year, current_time.month, current_time.day
        ) - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=7)

        remaining_tasks = []

        # Проходим по всем задачам группы
        for task in tasks:
            # Получаем количество выполненных задач за текущую неделю
            completed_count = await session.execute(
                select(Log).where(
                    Log.task_id == task.id,
                    Log.status == "completed",
                    Log.timestamp >= week_start,
                    Log.timestamp <= week_end,
                )
            )
            completed_count = len(completed_count.scalars().all())

            # Если выполнено меньше, чем требуется, добавляем в список оставшихся
            if completed_count < task.frequency:
                remaining_tasks.append(
                    (task.id, task.title, task.cost, task.frequency - completed_count)
                )

        if remaining_tasks:
            # Создаем клавиатуру с кнопками для выбора задачи
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"{title} - {cost} юнитов",
                            callback_data=f"task_{task_id}_{remaining}",
                        )
                    ]
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

        task = await session.execute(
            select(Task).where(Task.id == task_id, Task.group_id == user.group_id)
        )
        task = task.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Сделано", callback_data=f"done_{task_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отказаться", callback_data=f"cancel_{task_id}"
                    )
                ],
            ]
        )

        await callback.message.edit_text(
            f"Задача: {task.title}\nСтоимость: {task.cost} юнитов\nОсталось: {int(callback.data.split('_')[2])}",
            reply_markup=keyboard,
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
        tasks = await session.execute(
            select(Task).where(Task.group_id == group_id, Task.status == True)
        )
        tasks = tasks.scalars().all()

        if not tasks:
            await callback.message.edit_text("📭 В группе пока нет задач.")
            return

        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()

        # Фильтруем логи за текущую неделю
        current_time = datetime.now()
        week_start = datetime(
            current_time.year, current_time.month, current_time.day
        ) - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=group.sprint_duration)
        remaining_tasks = []

        # Проходим по всем задачам группы
        for task in tasks:
            # Получаем количество выполненных задач за текущую неделю
            completed_count = await session.execute(
                select(Log).where(
                    Log.task_id == task.id,
                    Log.status == "completed",
                    Log.timestamp >= week_start,
                    Log.timestamp <= week_end,
                )
            )
            completed_count = len(completed_count.scalars().all())

            # Если выполнено меньше, чем требуется, добавляем в список оставшихся
            if completed_count < task.frequency:
                remaining_tasks.append(
                    (task.id, task.title, task.cost, task.frequency - completed_count)
                )

        if remaining_tasks:
            # Создаем клавиатуру с кнопками для выбора задачи
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"{title} - {cost} юнитов",
                            callback_data=f"task_{task_id}_{remaining}",
                        )
                    ]
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
        task = await session.execute(
            select(Task).where(Task.id == task_id, Task.group_id == group_id)
        )
        task = task.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        # Получаем всех участников группы
        group_members = await session.execute(
            select(User).where(User.group_id == group_id)
        )
        group_members = group_members.scalars().all()

        # Если в группе только один участник, сразу подтверждаем задачу как выполненную
        if len(group_members) == 1:
            log = Log(
                group_id=group_id,
                user_id=user_id,
                task_id=task_id,
                status="completed",
                timestamp=datetime.now(),
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
            timestamp=datetime.now(),
        )
        session.add(log)
        await session.commit()

        # Получаем ID созданного лога
        log_id = log.id

        # Кнопки подтверждения и отказа
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"confirm_{task_id}_{log_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ Отказать", callback_data=f"reject_{task_id}_{log_id}"
                    )
                ],
            ]
        )

        # Уведомляем остальных участников группы
        for member in group_members:
            if member.id != user_id:
                await bot.send_message(
                    member.id,
                    f"📋 Пользователь {callback.from_user.first_name} отметил задачу '{task.title}' как выполненную. Ожидается ваше подтверждение.",
                    reply_markup=keyboard,
                )

        await callback.message.edit_text(
            f"⏳ Задача '{task.title}' отмечена как выполненная. Ожидание подтверждения..."
        )


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
        task = await session.execute(
            select(Task).where(Task.id == task_id, Task.group_id == group_id)
        )
        task = task.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        task_title = task.title

        # Находим лог по log_id
        log = await session.execute(
            select(Log).where(
                Log.id == log_id,
                Log.task_id == task_id,
                Log.status == "pending",
                Log.group_id == group_id,
            )
        )

        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()
        log = log.scalar_one_or_none()

        if not log:
            await callback.answer(
                "❌ Задача не найдена или уже подтверждена.", show_alert=True
            )
            return

        # Проверяем, сколько раз задача уже была выполнена за текущий спринт
        sprint_start = get_sprint_start_date(group.start_day)
        sprint_end = sprint_start + timedelta(days=group.sprint_duration)

        completed_count = await session.execute(
            select(func.count(Log.id)).where(
                Log.task_id == task_id,
                Log.status == "completed",
                Log.timestamp >= sprint_start,
                Log.timestamp <= sprint_end,
            )
        )
        completed_count = completed_count.scalar()

        # Если лимит выполнений исчерпан, отменяем подтверждение
        if completed_count >= task.frequency:
            await callback.answer(
                "❌ Лимит выполнений задачи исчерпан.", show_alert=True
            )
            await callback.message.edit_text(f"❌ Лимит выполнений задачи исчерпан.")
            await bot.send_message(
                log.user_id, f"❌ Лимит выполнений '{task_title}' исчерпан."
            )
            return

        # Обновляем лог на "выполнено"
        log.status = "completed"
        log.timestamp = datetime.now()
        await session.commit()

        await callback.message.edit_text(
            f"✅ Задача '{task_title}' подтверждена как выполненная."
        )

        # Уведомляем пользователя, который выполнял задачу
        await bot.send_message(
            log.user_id,
            f"✅ Ваша задача '{task_title}' была подтверждена как выполненная.",
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
        task = await session.execute(
            select(Task).where(
                Task.id == task_id,
                Task.group_id == user.group_id,
            )
        )
        task = task.scalar_one_or_none()

        if user is None or user.group_id is None:
            await message.answer("❌ Ты не состоишь в группе.", show_alert=True)
            return

        task = await session.execute(
            select(Task).where(
                Task.id == task_id,
                Task.group_id == user.group_id,
            )
        )
        task = task.scalar_one_or_none()
        task_title = task.title
        await session.commit()

        log = await session.execute(
            select(Log).where(
                Log.id == task_owner_id,
            )
        )
        log = log.scalar_one_or_none()

        # Отправляем причину отказа пользователю, который выполнял задачу
        await bot.send_message(
            log.user_id,
            f"❌ Ваша задача '{task_title}' не была подтверждена.\nПричина отказа: {reason}",
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
        tasks = await session.execute(
            select(Task).where(Task.group_id == group_id, Task.status == True)
        )
        tasks = tasks.scalars().all()

        if not tasks:
            await message.answer("❌ Для вашей группы нет задач.")
            return

        # Создаем клавиатуру с кнопками для выбора задачи
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{task.title}", callback_data=f"detail_{task.id}"
                    )
                ]
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
        task = await session.execute(
            select(Task).where(Task.id == task_id, Task.group_id == group_id)
        )
        task = task.scalar_one_or_none()
        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()

        if not task:
            await callback.answer("❌ Задача не найдена.", show_alert=True)
            return

        # Фильтруем логи за текущую неделю
        current_time = datetime.now()
        week_start = datetime(
            current_time.year, current_time.month, current_time.day
        ) - timedelta(days=current_time.weekday())
        week_end = week_start + timedelta(days=group.sprint_duration)

        # Получаем количество выполненных задач за текущую неделю
        completed_count = await session.execute(
            select(Log).where(
                Log.task_id == task.id,
                Log.status == "completed",
                Log.timestamp >= week_start,
                Log.timestamp <= week_end,
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
            "Чтобы прибавить или удалить 1 задачу, нажмите ➕ / ➖"
        )

        # Кнопка "Назад"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад", callback_data="back_to_task_list"
                    ),
                    InlineKeyboardButton(
                        text="➕",
                        callback_data=f"add_one_task_{remaining_tasks}_{task.id}",
                    ),
                    InlineKeyboardButton(
                        text="➖",
                        callback_data=f"minus_one_task_{remaining_tasks}_{task.id}",
                    ),
                ]
            ]
        )

        await callback.message.edit_text(response, reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("minus_one_task_"))
async def minus_one_task(callback: CallbackQuery):
    """Снижает частоту выполнения на 1."""

    remaining_tasks = int(callback.data.split("_")[-2])

    if remaining_tasks < 1:
        await callback.message.answer("Задачи все выполнены, удалить нельзя")
        return

    user_id = callback.from_user.id
    task_id = int(callback.data.split("_")[-1])

    async with async_session() as session:

        async with session.begin():
            query = select(User).filter(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            query = select(Task).filter(
                Task.id == task_id, Task.group_id == user.group_id
            )
            result = await session.execute(query)
            task = result.scalar_one_or_none()

            if task:

                if task.frequency - 1 < 0:
                    await callback.message.answer("Частота выполнения меньше 0.")
                    return

                task.frequency -= 1

                # Кнопка "Назад"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ Назад", callback_data="back_to_task_list"
                            ),
                            InlineKeyboardButton(
                                text="➕",
                                callback_data=f"add_one_task_{remaining_tasks - 1}_{task.id}",
                            ),
                            InlineKeyboardButton(
                                text="➖",
                                callback_data=f"minus_one_task_{remaining_tasks - 1}_{task.id}",
                            ),
                        ]
                    ]
                )

                await callback.message.edit_text(
                    f"🔹 Задача ID: {task.id}\n"
                    f"Название: {task.title}\n"
                    f"Частота выполнения: {task.frequency}\n"
                    f"Стоимость: {task.cost} ю\n"
                    f"Осталось выполнить: {remaining_tasks - 1} раз(а) на текущий спринт\n"
                    "Чтобы прибавить или удалить 1 задачу, нажмите ➕ / ➖",
                    reply_markup=keyboard,
                )

                await session.commit()


@router.callback_query(lambda c: c.data.startswith("add_one_task_"))
async def add_one_task(callback: CallbackQuery):
    """Увеличивает частоту выполнения на 1."""

    remaining_tasks = int(callback.data.split("_")[-2])

    user_id = callback.from_user.id
    task_id = int(callback.data.split("_")[-1])

    async with async_session() as session:

        async with session.begin():
            query = select(User).filter(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            query = select(Task).filter(
                Task.id == task_id, Task.group_id == user.group_id
            )
            result = await session.execute(query)
            task = result.scalar_one_or_none()

            if task:

                task.frequency += 1

                # Кнопка "Назад"
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="⬅️ Назад", callback_data="back_to_task_list"
                            ),
                            InlineKeyboardButton(
                                text="➕",
                                callback_data=f"add_one_task_{remaining_tasks + 1}_{task.id}",
                            ),
                            InlineKeyboardButton(
                                text="➖",
                                callback_data=f"minus_one_task_{remaining_tasks + 1}_{task.id}",
                            ),
                        ]
                    ]
                )

                await callback.message.edit_text(
                    f"🔹 Задача ID: {task.id}\n"
                    f"Название: {task.title}\n"
                    f"Частота выполнения: {task.frequency}\n"
                    f"Стоимость: {task.cost} ю\n"
                    f"Осталось выполнить: {remaining_tasks + 1} раз(а) на текущий спринт\n"
                    "Чтобы прибавить или удалить 1 задачу, нажмите ➕ / ➖",
                    reply_markup=keyboard,
                )

                await session.commit()


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
        tasks = await session.execute(
            select(Task).where(Task.group_id == group_id, Task.status == True)
        )
        tasks = tasks.scalars().all()

        if not tasks:
            await callback.message.edit_text("❌ Для вашей группы нет задач.")
            return

        # Создаем клавиатуру с кнопками для выбора задачи
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"{task.title}", callback_data=f"detail_{task.id}"
                    )
                ]
                for task in tasks
            ]
        )

        await callback.message.edit_text("📋 Список задач:", reply_markup=keyboard)


exit_codes = {}  # Храним коды подтверждения {user_id: код}


class ConfirmState(StatesGroup):
    """Состояния для подтверждения выхода и выбора нового владельца."""

    wait_confirm = State()  # Ожидание ввода кода подтверждения выхода


@router.message(Command("kill_tasks"))
async def kill_tasks(message: Message, state: FSMContext):
    """Запрос на удаление всех задач, отправляет код подтверждения."""
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.get(User, user_id)

        if not user or not user.group_id:
            await message.answer("❌ Ты не состоишь в группе.")
            return

        # Генерируем 4-значный код
        code = random.randint(1000, 9999)
        exit_codes[user_id] = code

        await state.set_state(ConfirmState.wait_confirm)
        await message.answer(
            f"⚠️ Ты собираешься очистить все задачи. Чтобы подтвердить, введи код: `{code}`",
            parse_mode="Markdown",
        )


@router.message(ConfirmState.wait_confirm)
async def confirm_kill(message: Message, state: FSMContext):
    """Убирает все оставшиеся задачи."""

    user_id = message.from_user.id

    if user_id in exit_codes and message.text == str(exit_codes[user_id]):

        async with async_session() as session:
            # Проверяем, состоит ли пользователь в группе
            user = await session.execute(select(User).where(User.id == user_id))
            user = user.scalar_one_or_none()

            if user is None or user.group_id is None:
                await message.answer("❌ Ты не состоишь в группе.")
                return

            group_id = user.group_id

            # Получаем все задачи группы
            tasks = await session.execute(
                select(Task).where(Task.group_id == group_id, Task.status == True)
            )
            tasks = tasks.scalars().all()

            if not tasks:
                await message.answer("📭 В группе пока нет задач.")
                return

            # Фильтруем логи за текущую неделю
            current_time = datetime.now()
            week_start = datetime(
                current_time.year, current_time.month, current_time.day
            ) - timedelta(days=current_time.weekday())
            week_end = week_start + timedelta(days=7)

            remaining_tasks = []

            # Проходим по всем задачам группы
            for task in tasks:
                # Получаем количество выполненных задач за текущую неделю
                completed_count = await session.execute(
                    select(Log).where(
                        Log.task_id == task.id,
                        Log.status == "completed",
                        Log.timestamp >= week_start,
                        Log.timestamp <= week_end,
                    )
                )
                completed_count = len(completed_count.scalars().all())

                # Если выполнено меньше, чем требуется,
                # добавляем в список оставшихся
                if completed_count < task.frequency:
                    remaining_tasks.append(
                        (
                            task.id,
                            task.title,
                            task.cost,
                            task.frequency - completed_count,
                        )
                    )

        async with async_session() as session:

            if remaining_tasks:
                # Удаляем оставшиеся задачи
                async with session.begin():
                    query = select(User).filter(User.id == user_id)
                    result = await session.execute(query)
                    user = result.scalar_one_or_none()

                    for task in remaining_tasks:
                        query = select(Task).filter(
                            Task.id == task[0], Task.group_id == user.group_id
                        )
                        result = await session.execute(query)
                        task_ = result.scalar_one_or_none()

                        if task_:
                            task_.frequency -= task[-1]

                    await session.commit()
                    await message.answer("Оставшиеся задачи очищены")

            else:
                await message.answer("Не осталось задач")

    elif user_id in exit_codes:
        await message.answer("❌ Неверный код. Попробуй еще раз.")
