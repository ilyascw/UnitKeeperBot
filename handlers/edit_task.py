from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.models import User, Task
from db.database import async_session

router = Router()

class EditTaskState(StatesGroup):
    wait_task_id = State()
    wait_new_title = State()
    wait_new_frequency = State()
    wait_new_cost = State()

@router.message(Command("edit_task"))
async def edit_task_start(message: Message, state: FSMContext):
    """Начало редактирования задачи по ID"""
    user_id = message.from_user.id
    
    # Получаем пользователя и его группу из БД
    async with async_session() as session:
        async with session.begin():
            query = select(User).filter(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

    if user is None:
        await message.answer("❌ Ты не состоишь в группе.")
        return

    await message.answer("Введите ID задачи, которую хотите отредактировать:\nID задачи можно посмотреть с помощью команды /list_of_tasks")
    await state.set_state(EditTaskState.wait_task_id)

@router.message(EditTaskState.wait_task_id)
async def edit_task_id(message: Message, state: FSMContext):
    """Проверяем, существует ли задача с таким ID"""
    user_id = message.from_user.id
    try:
        task_id = int(message.text)
        
        # Получаем задачу из БД по ID
        async with async_session() as session:
            async with session.begin():
                query = select(User).filter(User.id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()

        if task is None:
            await message.answer("❌ Задача с таким ID не найдена в вашей группе. Попробуйте снова.")
            return

        # Отправляем пользователю возможность изменить название
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="оставить старое")],
            ],
            resize_keyboard=True
        )

        await state.update_data(task_id=task_id)
        await message.answer("Введите новое название задачи:", reply_markup=keyboard)
        await state.set_state(EditTaskState.wait_new_title)
    except ValueError:
        await message.answer("❌ ID задачи должно быть числом. Попробуйте снова.")

@router.message(EditTaskState.wait_new_title)
async def edit_task_title(message: Message, state: FSMContext):
    """Запоминаем новое название задачи"""
    data = await state.get_data()
    task_id = data["task_id"]
    user_id = message.from_user.id

    if message.text == 'оставить старое':
        # Получаем текущую задачу из БД
        async with async_session() as session:
            async with session.begin():
                query = select(User).filter(User.id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()
        
        if task:
            new_title = task.title
    else:
        new_title = message.text

    # Обновляем название задачи в БД
    async with async_session() as session:
        async with session.begin():
            query = select(User).filter(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
            result = await session.execute(query)
            task = result.scalar_one_or_none()
            
            if task:
                task.title = new_title
                await session.commit()

    await state.update_data(new_title=new_title)
    await message.answer(f"Название задачи успешно обновлено на: {new_title}. Введите новую частоту выполнения:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(EditTaskState.wait_new_frequency)

@router.message(EditTaskState.wait_new_frequency)
async def edit_task_frequency(message: Message, state: FSMContext):
    """Запоминаем новую частоту выполнения задачи"""
    data = await state.get_data()
    task_id = data["task_id"]
    try:
        new_frequency = int(message.text)
        user_id = message.from_user.id

        # Обновляем частоту задачи в БД
        async with async_session() as session:
            async with session.begin():
                query = select(User).filter(User.id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()

                if task:
                    task.frequency = new_frequency
                    await session.commit()

        await state.update_data(new_frequency=new_frequency)
        await message.answer(f"Частота выполнения задачи обновлена на: {new_frequency} раз в неделю. Введите новую стоимость:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(EditTaskState.wait_new_cost)
    except ValueError:
        await message.answer("❌ Частота выполнения должна быть числом. Попробуйте снова.", reply_markup=ReplyKeyboardRemove())

@router.message(EditTaskState.wait_new_cost)
async def edit_task_cost(message: Message, state: FSMContext):
    """Запоминаем новую стоимость задачи"""
    data = await state.get_data()
    task_id = data["task_id"]
    try:
        new_cost = int(message.text)
        user_id = message.from_user.id

        # Обновляем стоимость задачи в БД
        async with async_session() as session:
            async with session.begin():
                query = select(User).filter(User.id == user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                query = select(Task).filter(Task.id == task_id, Task.group_id == user.group_id)
                result = await session.execute(query)
                task = result.scalar_one_or_none()

                if task:
                    task.cost = new_cost
                    await session.commit()

        await message.answer(f"Стоимость задачи обновлена на: {new_cost}.\n\nЗадача обновлена!")
        await state.clear()  # Очищаем состояние
    except ValueError:
        await message.answer("❌ Стоимость должна быть числом. Попробуйте снова.")