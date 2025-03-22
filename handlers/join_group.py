# Основные импорты aiogram
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    ReplyKeyboardRemove
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


class JoinGroupState(StatesGroup):
    waiting_for_group_id = State()
    waiting_for_password = State()

@router.message(Command("join_group"))
@router.message(F.text == "🔑 Вступить в группу")
async def join_group_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    async with async_session() as session:
        user = await session.get(User, user_id)
        if user and user.group_id:
            await message.answer("❌ Для начала надо выйти из группы.\nДля выхода: /exit_group")
            return

    await message.answer("Введите название группы, в которую хотите вступить:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(JoinGroupState.waiting_for_group_id)


@router.message(JoinGroupState.waiting_for_group_id)
async def join_group_id(message: Message, state: FSMContext):
    name = message.text

    if not re.match(r'^[A-Za-z0-9_а-яА-ЯёЁ]+$', name):
        await message.answer("❌ Название группы может содержать только буквы, цифры и символы подчеркивания.")
        return
    
    async with async_session() as session:
        # Получаем группу по имени
        group = await session.execute(select(Group).where(Group.name == name))
        group = group.scalars().first()

        if not group:
            await message.answer("❌ Группа не найдена. Введите имя снова.")
            return
        
        # Сохраняем group_id в состояние
        await state.update_data(group_id=group.id)

        await message.answer("Введите пароль группы:")
        await state.set_state(JoinGroupState.waiting_for_password)


@router.message(JoinGroupState.waiting_for_password)
async def join_group_password(message: Message, state: FSMContext):
    data = await state.get_data()
    group_id = data["group_id"]
    user_id = message.from_user.id

    async with async_session() as session:
        # Получаем информацию о группе
        group = await session.get(Group, group_id)
        if not group or group.password != message.text:
            await message.answer("❌ Неверный пароль. Попробуйте снова.")
            return

        # Получаем информацию о пользователе
        user = await session.get(User, user_id)
        if not user:
            # Добавляем нового пользователя в таблицу Users
            user = User(id=user_id, group_id=group_id)
            session.add(user)
            await session.commit()  # Подтверждаем изменения в таблице Users
        else:
            user.group_id = group_id

        # Проверка существования записи в таблице Balance
        balance_entry = await session.execute(
            select(Balance).where(Balance.user_id == user_id, Balance.group_id == group_id)
        )
        existing_balance = balance_entry.scalars().first()

        if not existing_balance:
            # Добавляем новую запись в таблицу Balance, если такой записи нет
            balance_entry = Balance(user_id=user_id, group_id=group_id, balance=0)
            session.add(balance_entry)

        # Если нагрузка отсутствует, создаем новый словарь
        if not group.weights:
            group.weights = {}

        if not group.owner_id:
            group.owner_id = message.from_user.id

    # Удаляем пользователя из weights и пересчитываем нагрузку
        weights = group.weights.copy()
        weights[f'{user_id}'] = 0
        num_members = len(weights)
        new_balance = (100 / num_members)
        weights = {k: new_balance for k in weights.keys()}
        group.weights = weights
        await session.commit()  # Подтверждаем изменения в таблицах Users, Balance и Group

        await message.answer(f"✅ Вы успешно вступили в группу {group.name}!", reply_markup=ReplyKeyboardRemove())
        await state.clear()