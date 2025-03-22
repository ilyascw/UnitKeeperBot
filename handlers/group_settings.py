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
from db.database import async_session
from db.models import Group, User

import re

router = Router()


class GroupSettingsState(StatesGroup):
    waiting_for_start_day = State()
    waiting_for_password = State()
    waiting_for_sprint_duration = State()
    waiting_for_user_weight = State()

@router.message(Command("group_settings"))
async def group_settings_start(message: Message, state: FSMContext):
    """Начало изменения настроек группы."""
    user_id = message.from_user.id

    async with async_session() as session:
        # Получаем пользователя и его группу
        user = await session.execute(select(User).where(User.id == user_id))
        user = user.scalar_one_or_none()

        if user is None or user.group_id is None:
            await message.answer("❌ Вы не состоите в группе.")
            return

        # Получаем группу
        group = await session.execute(select(Group).where(Group.id == user.group_id))
        group = group.scalar_one_or_none()

        if group is None:
            await message.answer("❌ Группа не найдена.")
            return

        # Проверяем, является ли пользователь владельцем группы
        if group.owner_id != user_id:
            await message.answer("❌ Только владелец группы может изменять настройки.")
            return

        # Сохраняем ID группы в состоянии
        await state.update_data(group_id=group.id)

        # Создаем клавиатуру для выбора действия
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Изменить день начала", callback_data="change_start_day")],
                [InlineKeyboardButton(text="Изменить пароль", callback_data="change_password")],
                [InlineKeyboardButton(text="Изменить длительность спринта", callback_data="change_sprint_duration")],
                [InlineKeyboardButton(text="Изменить нагрузку участников", callback_data="change_weights")],
            ]
        )

        await message.answer("⚙️ Настройки группы:", reply_markup=keyboard)

@router.callback_query(F.data == "change_start_day")
async def change_start_day(callback: CallbackQuery, state: FSMContext):
    """Изменение дня начала спринта."""
    # Создаем клавиатуру с днями недели
    days_of_week = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=day, callback_data=f"set_start_day_{day}")] for day in days_of_week
        ]
    )

    await callback.message.edit_text("Выберите новый день начала спринта:", reply_markup=keyboard)
    await state.set_state(GroupSettingsState.waiting_for_start_day)

@router.callback_query(F.data.startswith("set_start_day_"))
async def set_start_day(callback: CallbackQuery, state: FSMContext):
    """Установка нового дня начала спринта."""
    start_day = callback.data.split("_")[3]  # Извлекаем день недели из callback_data

    async with async_session() as session:
        data = await state.get_data()
        group_id = data["group_id"]

        # Обновляем день начала спринта в базе данных
        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()

        if group:
            group.start_day = start_day
            await session.commit()

        await callback.message.edit_text(f"✅ День начала спринта изменен на: {start_day}.")
        await state.clear()

@router.callback_query(F.data == "change_password")
async def change_password(callback: CallbackQuery, state: FSMContext):
    """Изменение пароля группы."""
    await callback.message.edit_text("Введите новый пароль для группы:")
    await state.set_state(GroupSettingsState.waiting_for_password)

@router.message(GroupSettingsState.waiting_for_password)
async def set_password(message: Message, state: FSMContext):
    """Установка нового пароля группы."""
    password = message.text

    # Проверяем, что пароль состоит только из допустимых символов
    if not re.match(r'^[A-Za-z0-9_]+$', password):
        await message.answer("❌ Пароль может содержать только латинские буквы, цифры и символы подчеркивания.")
        return

    async with async_session() as session:
        data = await state.get_data()
        group_id = data["group_id"]

        # Обновляем пароль в базе данных
        group = await session.execute(select(Group).where(Group.id == group_id))
        group = group.scalar_one_or_none()

        if group:
            group.password = password
            await session.commit()

        await message.answer("✅ Пароль группы успешно изменен.")
        await state.clear()

@router.callback_query(F.data == "change_sprint_duration")
async def change_sprint_duration(callback: CallbackQuery, state: FSMContext):
    """Изменение длительности спринта."""
    await callback.message.edit_text("Введите новую длительность спринта (в днях):")
    await state.set_state(GroupSettingsState.waiting_for_sprint_duration)

@router.message(GroupSettingsState.waiting_for_sprint_duration)
async def set_sprint_duration(message: Message, state: FSMContext):
    """Установка новой длительности спринта."""
    try:
        sprint_duration = int(message.text)

        async with async_session() as session:
            data = await state.get_data()
            group_id = data["group_id"]

            # Обновляем длительность спринта в базе данных
            group = await session.execute(select(Group).where(Group.id == group_id))
            group = group.scalar_one_or_none()

            if group:
                group.sprint_duration = sprint_duration
                await session.commit()

            await message.answer(f"✅ Длительность спринта изменена на: {sprint_duration} дней.")
            await state.clear()
    except ValueError:
        await message.answer("❌ Длительность должна быть числом. Введите снова.")

@router.callback_query(F.data == "change_weights")
async def change_weights(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Изменение нагрузки участников."""
    async with async_session() as session:
        # Получаем данные из состояния
        data = await state.get_data()
        print(data.items())
        group_id = data["group_id"]

        # Получаем всех участников группы
        users = await session.execute(select(User).where(User.group_id == group_id))
        users = users.scalars().all()

        if not users:
            await callback.message.edit_text("❌ В группе нет участников.")
            return

        # Сохраняем список пользователей в состоянии
        await state.update_data(users=[user.id for user in users], current_user_index=0, group_id=group_id)

        # Запрашиваем нагрузку для первого пользователя
        await ask_user_weight(callback.message, state, bot)

async def ask_user_weight(message: Message, state: FSMContext, bot: Bot):
    """Запрос нагрузки для конкретного пользователя."""
    data = await state.get_data()
    users = data["users"]
    current_user_index = data["current_user_index"]

    # Если все пользователи обработаны
    if current_user_index >= len(users):
        await message.answer("✅ Нагрузка для всех участников обновлена.")
        await state.clear()
        return

    user_id = users[current_user_index]

    # Получаем first_name пользователя через API Telegram
    try:
        user_chat = await bot.get_chat(user_id)
        first_name = user_chat.first_name
    except Exception as e:
        print(f"Ошибка при получении имени пользователя: {e}")
        first_name = "Пользователь"

    await message.answer(f"Нагрузка у всех пользователей в сумме должна быть 100.")
    await message.answer(f"Введите новую нагрузку для пользователя (от 1 до 100) {first_name} (ID: {user_id}):")
    await state.set_state(GroupSettingsState.waiting_for_user_weight)

@router.message(GroupSettingsState.waiting_for_user_weight)
async def set_user_weight(message: Message, state: FSMContext, bot: Bot):
    """Установка новой нагрузки для пользователя."""
    try:
        weight = float(message.text)

        # Проверка, что нагрузка в пределах от 0 до 100
        if weight > 100 or weight < 0:
            await message.answer('Нагрузка должна быть в промежутке от 0 до 100.')
            return

        async with async_session() as session:
            data = await state.get_data()
            group_id = data["group_id"]
            users = data["users"]
            current_user_index = data["current_user_index"]

            user_id = users[current_user_index]

            # Получаем first_name пользователя через API Telegram
            try:
                user_chat = await bot.get_chat(user_id)
                first_name = user_chat.first_name
            except Exception as e:
                print(f"Ошибка при получении имени пользователя: {e}")
                first_name = "Пользователь"

            # Получаем группу
            group = await session.execute(select(Group).where(Group.id == group_id))
            group = group.scalar_one_or_none()

            if not group:
                await message.answer("❌ Группа не найдена.")
                return

            # Получаем текущие нагрузки
            weights = group.weights if group.weights else {}

            # Обновляем нагрузку для текущего пользователя
            weights[str(user_id)] = weight

            # Сохраняем обновленные нагрузки в группе
            group.weights = weights
            await session.commit()

            # Проверка, что все пользователи обработаны
            if current_user_index + 1 >= len(users):
                # Проверка, что сумма нагрузок равна 100
                if sum(weights.values()) != 100:
                    await message.answer(f'Нагрузка должна быть в сумме 100, а не {sum(weights.values())}.')
                    return

                await message.answer("✅ Нагрузки для всех пользователей успешно установлены!")
                await state.clear()  # Завершаем состояние
            else:
                # Переходим к следующему пользователю
                await state.update_data(current_user_index=current_user_index + 1)
                await ask_user_weight(message, state, bot)

    except ValueError:
        await message.answer("❌ Нагрузка должна быть числом. Введите снова.")