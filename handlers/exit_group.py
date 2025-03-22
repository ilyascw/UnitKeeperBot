# Основные импорты aiogram
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импорты для работы с базой данных
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import async_session
from db.models import Group, User

# Дополнительные импорты
import random

router = Router()


        
exit_codes = {}  # Храним коды подтверждения {user_id: код}

class ConfirmState(StatesGroup):
    """Состояния для подтверждения выхода и выбора нового владельца."""
    
    wait_confirm = State()  # Ожидание ввода кода подтверждения выхода
    waiting_for_new_owner = State()  # Ожидание выбора нового владельца

@router.message(Command("exit_group"))
async def exit_group_request(message: Message, state: FSMContext):
    """Запрос на выход из группы, отправляет код подтверждения."""
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
        await message.answer(f"⚠️ Ты собираешься выйти из группы. Чтобы подтвердить, введи код: `{code}`", parse_mode="Markdown")


@router.message(ConfirmState.wait_confirm)
async def confirm_exit_group(message: Message, state: FSMContext):
    """Обрабатывает ввод кода подтверждения выхода."""
    user_id = message.from_user.id

    if user_id in exit_codes and message.text == str(exit_codes[user_id]):
        async with async_session() as session:
            user = await session.get(User, user_id)

            if not user or not user.group_id:
                await message.answer("❌ Ошибка: ты уже не состоишь в группе.")
                return

            group_id = user.group_id
            group = await session.get(Group, group_id)

            if not group or not group.weights:
                await message.answer("❌ Ошибка: не удалось найти данные о группе.")
                return

            # Удаляем пользователя из weights и пересчитываем нагрузку
            weights = group.weights.copy()
            weights.pop(str(user_id), None)

            num_members = len(weights)
            if num_members > 0:
                new_balance = 100 / num_members
                weights = {k: new_balance for k in weights}

            # Проверяем, кто остается владельцем
            if user_id == group.owner_id:
                await handle_owner_exit(message, state, session, group, weights)

            # Убираем пользователя из группы
            user.group_id = None
            group.weights = weights
            print(weights)
            
            try:
                await session.commit()
            except Exception as e:
                print(f'!!!!!!!!!!!!!!!!!!!!{e}')

            del exit_codes[user_id]

            await message.answer("✅ Ты вышел из группы.")
            await state.clear()

    elif user_id in exit_codes:
        await message.answer("❌ Неверный код. Попробуй еще раз.")


async def handle_owner_exit(message: Message, state: FSMContext, session: AsyncSession, group: Group, weights: dict):
    """Обрабатывает смену владельца при выходе текущего владельца."""
    num_members = len(weights)

    if num_members > 1:
        # Запрашиваем у владельца выбор нового
        users_in_group = await session.execute(select(User).where(User.group_id == group.id))
        users_in_group = users_in_group.scalars().all()

        buttons = [
            InlineKeyboardButton(f"{u.username or u.first_name}", callback_data=f"new_owner:{u.id}")
            for u in users_in_group if u.id != group.owner_id
        ]

        if buttons:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
            await message.answer("Выберите нового владельца группы:", reply_markup=keyboard)
            await state.set_state(ConfirmState.waiting_for_new_owner)
            await state.update_data(group_id=group.id, users=users_in_group)
        else:
            await auto_assign_owner(message, state, session, group, weights)

    else:
        # Если один человек остался, он становится владельцем, иначе группа без владельца
        group.owner_id = int(list(weights.keys())[0]) if num_members == 1 else None
        await session.commit()


@router.message(ConfirmState.waiting_for_new_owner)
async def enforce_owner_selection(message: Message, state: FSMContext):
    """Напоминает выбрать владельца или автоматически назначает его."""
    data = await state.get_data()
    group_id = data.get("group_id")
    users = data.get("users")

    if not group_id or not users:
        await message.answer("❌ Ошибка при смене владельца.")
        await state.clear()
        return

    if "reminder_sent" in data:
        await auto_assign_owner(message, state, async_session(), group_id, users)
    else:
        await message.answer("⚠️ Сначала выбери нового владельца группы.")
        await state.update_data(reminder_sent=True)


async def auto_assign_owner(message: Message, state: FSMContext, session: AsyncSession, group_id: int, users):
    """Автоматически назначает первого из списка владельцем, если не был выбран."""
    group = await session.get(Group, group_id)

    if not group or not users:
        await message.answer("❌ Ошибка: не удалось сменить владельца.")
        return

    new_owner = users[0]
    group.owner_id = new_owner.id
    await session.commit()

    await message.answer(f"✅ Новый владелец группы: {new_owner.username or new_owner.first_name}.")
    await state.clear()


@router.callback_query(lambda query: query.data.startswith("new_owner:"))
async def select_new_owner(callback_query: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор нового владельца из инлайн-кнопок."""
    new_owner_id = int(callback_query.data.split(":")[1])

    async with async_session() as session:
        data = await state.get_data()
        group_id = data.get("group_id")

        if not group_id:
            await callback_query.message.answer("❌ Ошибка: не найдена группа.")
            return

        group = await session.get(Group, group_id)
        new_owner = await session.get(User, new_owner_id)

        if new_owner and group:
            group.owner_id = new_owner.id
            await session.commit()

            await callback_query.message.edit_text(f"✅ Новый владелец группы: {new_owner.username or new_owner.first_name}.")
            await state.clear()
        else:
            await callback_query.message.answer("❌ Ошибка: не удалось назначить нового владельца.")