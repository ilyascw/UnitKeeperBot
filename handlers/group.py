# Основные импорты aiogram
from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импорты для работы с базой данных
from sqlalchemy import select
from db.database import async_session
from db.models import Group, User, Balance

import re

router = Router()

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """
    Обработчик команды /cancel.
    Очищает текущее состояние пользователя.
    """
    # Очищаем состояние
    await state.clear()

    # Отправляем сообщение пользователю
    await message.answer(
        "❌ Действие отменено. Все состояния очищены.",
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру, если она есть
    )

class CreateGroupState(StatesGroup):
    waiting_for_name = State()
    waiting_for_password = State()
    waiting_for_start_day = State()  # Новый шаг для дня начала
    waiting_for_sprint_duration = State()  # Новый шаг для длительности


@router.message(Command("create_group"))
@router.message(F.text == "➕ Создать группу")
async def create_group_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Проверяем, состоит ли пользователь уже в группе
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.group_id:
            await message.answer("❌ Для начала надо выйти из группы.\nДля выхода из группы: /exit_group")
            return

    await message.answer("Введите название новой группы:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CreateGroupState.waiting_for_name)

@router.message(CreateGroupState.waiting_for_name)
async def create_group_name(message: Message, state: FSMContext):
            # Проверка уникальности имени группы

    group_name = message.text

    async with async_session() as session:
        # Проверяем, существует ли уже группа с таким названием
        group_check = await session.execute(select(Group).where(Group.name == group_name))
        existing_group = group_check.scalars().first()

        if existing_group:
            await message.answer(f"❌ Группа с названием '{group_name}' уже существует. Пожалуйста, выберите другое имя.")
            return

        # Проверяем, что имя группы состоит только из допустимых символов (буквы, цифры)
        if not re.match(r'^[A-Za-z0-9_а-яА-ЯёЁ]+$', group_name):
            await message.answer("❌ Название группы может содержать только буквы, цифры и символы подчеркивания.")
            return
        
    await state.update_data(group_name=message.text)
    await message.answer("Введите пароль для группы:")
    await state.set_state(CreateGroupState.waiting_for_password)

@router.message(CreateGroupState.waiting_for_password)
async def create_group_password(message: Message, state: FSMContext):
    
    # Проверяем, что пароль состоит только из допустимых символов (буквы, цифры)
    password=message.text

    if not re.match(r'^[A-Za-z0-9_]+$', password):
        await message.answer("❌ Пароль может содержать только латинские буквы, цифры и символы подчеркивания.")
        return
    
    await state.update_data(password=password)

    days_of_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=day)] for day in days_of_week],
        resize_keyboard=True
    )
    await message.answer("Введите день начала периода учета:", reply_markup=keyboard)
    await state.set_state(CreateGroupState.waiting_for_start_day)

@router.message(CreateGroupState.waiting_for_start_day)
async def create_group_start_day(message: Message, state: FSMContext):
    start_day = message.text.lower()
    if start_day not in ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]:
        await message.answer("❌ Введите корректный день недели.")
        return

    await state.update_data(start_day=start_day)
    await message.answer("Введите длительность периода учета в днях (число должно делиться нацело на 7):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CreateGroupState.waiting_for_sprint_duration)

@router.message(CreateGroupState.waiting_for_sprint_duration)
async def create_group_sprint_duration(message: Message, state: FSMContext):
    try:
        sprint_duration = int(message.text)

        if sprint_duration % 7 != 0:
            raise ValueError
        
        await state.update_data(sprint_duration=sprint_duration)

        data = await state.get_data()
        group_name = data["group_name"]
        password = data["password"]
        start_day = data["start_day"]
        owner_id = message.from_user.id

        async with async_session() as session:
            # Создаём новую группу
            new_group = Group(
                name=group_name,
                password=password,
                start_day=start_day,
                sprint_duration=sprint_duration,
                owner_id=owner_id,
                group_balance=0, 
                weights={str(message.from_user.id): 100}
            )
            session.add(new_group)
            await session.flush()  # Получаем ID новой группы
            
            user_id = message.from_user.id

            # Обновляем пользователя, привязывая его к группе
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if user:
                user.group_id = new_group.id  # Привязываем пользователя к группе
            else:
                session.add(User(id=user_id, group_id=new_group.id))  # Если пользователя нет — создаём

            await session.commit()

            # Добавляем запись в таблицу баланса
            stmt = select(Balance).where(Balance.user_id == user_id, Balance.group_id == new_group.id)
            result = await session.execute(stmt)
            balance_entry = result.scalars().first()

            if not balance_entry:
                session.add(Balance(user_id=user_id, group_id=new_group.id, balance=0))

            await session.commit()
        
        await message.answer(f"✅ Группа '{group_name}' успешно создана!")
        await state.clear()

    except ValueError:
        await message.answer("❌ Длительность должна быть числом, делящимся нацело на 7. Введите снова.")
        await state.set_state(CreateGroupState.waiting_for_sprint_duration)


