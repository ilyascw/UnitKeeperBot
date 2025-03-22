from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User, Task
from db.database import async_session
from sqlalchemy import delete

router = Router()

class DeleteTaskState(StatesGroup):
    wait_task_id = State()  # Состояние для ввода ID задачи
    confirm_deletion = State()  # Состояние для подтверждения 

@router.message(Command("delete_task"))
async def delete_task_start(message: Message, state: FSMContext):
    """Начало удаления задачи по ID"""
    user_id = message.from_user.id
    
    # Получаем группу пользователя из базы данных
    async with async_session() as session:
        query = select(User).filter(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

    if user is None:
        await message.answer("❌ Ты не состоишь в группе.")
        return

    await message.answer("Введите ID задачи, которую хотите удалить:\nID задачи можно посмотреть с помощью команды /list_of_tasks")
    await state.set_state(DeleteTaskState.wait_task_id)  # Переход к состоянию ожидания ID задачи

@router.message(DeleteTaskState.wait_task_id)
async def delete_task_id(message: Message, state: FSMContext):
    """Проверяем, существует ли задача с таким ID для удаления"""
    user_id = message.from_user.id
    try:
        task_id = int(message.text)  # Преобразуем введённый текст в число

        # Получаем пользователя и задачу из базы данных
        async with async_session() as session:
            query = select(User).filter(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user is None:
                await message.answer("❌ Ты не состоишь в группе.")
                return

            # Получаем задачу для этого пользователя и группы
            query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()

        if task is None:
            await message.answer("❌ Задача с таким ID не найдена. Попробуйте снова.")
            return

        # Сохраняем task_id в состоянии
        await state.update_data(task_id=task_id)

        # Создаем клавиатуру с кнопками подтверждения
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_{task_id}")],
                [InlineKeyboardButton(text="❌ Нет, отменить", callback_data="c_delete")]
            ]
        )

        # Отправляем сообщение с запросом подтверждения
        await message.answer(
            f"Вы уверены, что хотите удалить задачу '{task.title}'?",
            reply_markup=keyboard
        )

        # Переход к состоянию подтверждения удаления
        await state.set_state(DeleteTaskState.confirm_deletion)

    except ValueError:
        await message.answer("❌ ID задачи должно быть числом. Попробуйте снова.")

@router.callback_query(lambda c: c.data and c.data.startswith("delete_"))
async def confirm_delete_task(callback_query: CallbackQuery, state: FSMContext):
    """Подтверждаем удаление задачи"""
    task_id = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    # Получаем пользователя и задачу из базы данных
    async with async_session() as session:
        query = select(User).filter(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if user is None:
            await callback_query.message.edit_text("❌ Ты не состоишь в группе.")
            return

        # Получаем задачу для этого пользователя и группы
        query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
        result = await session.execute(query)
        task = result.scalar_one_or_none()

    if task is None:
        await callback_query.message.edit_text("❌ Задача не найдена.")
        return

    # Обновляем статус задачи на False, чтобы она считалась удаленной
    async with async_session() as session:
        task.status = False  # Помечаем задачу как удаленную
        session.add(task)
        await session.commit()

    # Отправляем ответ с подтверждением
    await callback_query.answer("✅ Задача помечена как удаленная.")  # Отправляет всплывающее уведомление
    await callback_query.message.edit_text(f"✅ Задача с ID {task_id} была помечена как удаленная.")

    await state.clear()  # Очищаем состояние

@router.callback_query(lambda c: c.data == "c_delete")
async def cancel_delete_task(callback_query: CallbackQuery, state: FSMContext):
    """Отменяем удаление задачи"""
    await callback_query.answer("❌ Удаление задачи отменено.")
    await callback_query.message.edit_text("❌ Удаление задачи было отменено.")  # Изменяем текст сообщения
    await state.clear()  # Очищаем состояние