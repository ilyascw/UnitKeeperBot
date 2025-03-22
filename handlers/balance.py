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
from db.models import User, Balance

router = Router()

# Состояния для перевода юнитов
class TransferUnitsState(StatesGroup):
    waiting_for_recipient = State()  # Ожидание выбора получателя
    waiting_for_amount = State()  # Ожидание ввода суммы

@router.message(Command("balance"))
async def balance(message: Message):
    """
    Обработчик команды /balance.
    Выводит меню с выбором: посмотреть баланс или перевести юниты.
    """
    # Создаем inline-кнопки
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть баланс", callback_data="view_balance")],
        [InlineKeyboardButton(text="Перевести юниты", callback_data="transfer_units")]
    ])

    await message.answer("Что требуется сделать?", reply_markup=keyboard)

@router.callback_query(F.data == "view_balance")
async def view_balance(callback_query: CallbackQuery):
    """
    Обработчик для кнопки "Посмотреть баланс".
    Выводит текущий баланс пользователя.
    """
    user_id = callback_query.from_user.id

    async with async_session() as session:
        # Получаем пользователя и его группу
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user or not user.group_id:
            await callback_query.answer("❌ Ты не состоишь в группе.")
            return

        # Получаем баланс пользователя
        stmt = select(Balance).where((Balance.user_id == user_id) & (Balance.group_id == user.group_id))
        result = await session.execute(stmt)
        balance = result.scalars().first()

        if not balance:
            await callback_query.answer("❌ Баланс не найден.")
            return

        # Отправляем сообщение с балансом
        await callback_query.message.edit_text(f"💰 Твой баланс: {balance.balance} юнитов.")


@router.callback_query(F.data == "transfer_units")
async def transfer_units_start(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик для кнопки "Перевести юниты".
    Выводит список участников группы для выбора получателя.
    """
    user_id = callback_query.from_user.id

    async with async_session() as session:
        # Получаем пользователя и его группу
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user or not user.group_id:
            await callback_query.answer("❌ Ты не состоишь в группе.")
            return

        # Получаем список участников группы
        stmt = select(User).where(User.group_id == user.group_id)
        result = await session.execute(stmt)
        members = result.scalars().all()

        # Создаем inline-кнопки с участниками группы
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"👤 {member.id}", callback_data=f"transfer_to_{member.id}")]
            for member in members if member.id != user_id  # Исключаем текущего пользователя
        ] + [
            [InlineKeyboardButton(text="Назад", callback_data="back_to_balance")]
        ])

        await callback_query.message.edit_text("Выберите участника для перевода:", reply_markup=keyboard)

        # Устанавливаем состояние ожидания выбора получателя
        await state.set_state(TransferUnitsState.waiting_for_recipient)

@router.callback_query(F.data.startswith("transfer_to_"))
async def choose_recipient(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик для выбора получателя.
    Сохраняет ID получателя и запрашивает количество юнитов.
    """
    recipient_id = int(callback_query.data.split("_")[2])

    # Сохраняем ID получателя в состоянии
    await state.update_data(recipient_id=recipient_id)

    # Запрашиваем количество юнитов
    await callback_query.message.answer("Введите количество юнитов для перевода:")

    # Устанавливаем состояние ожидания ввода количества юнитов
    await state.set_state(TransferUnitsState.waiting_for_amount)

@router.message(TransferUnitsState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext, bot: Bot):
    """
    Обработчик для ввода количества юнитов.
    Выполняет перевод, если у отправителя достаточно средств.
    """
    user_id = message.from_user.id
    amount = message.text

    # Проверяем, что введено число
    try:
        amount = float(amount)
        if amount <= 0:
            await message.answer("❌ Введите положительное число.")
            return
    except ValueError:
        await message.answer("❌ Введите число.")
        return
    
    async with async_session() as session:
        # Получаем данные из состояния
        data = await state.get_data()
        recipient_id = data['recipient_id']

        # Получаем баланс отправителя
        stmt = select(Balance).where((Balance.user_id == user_id) & (Balance.group_id == User.group_id))
        result = await session.execute(stmt)
        sender_balance = result.scalars().first()

        if not sender_balance or sender_balance.balance < amount:
            await message.answer("❌ Недостаточно юнитов для перевода. Попробуйте позже.")
            await state.clear()
            return

        # Получаем баланс получателя
        stmt = select(Balance).where((Balance.user_id == recipient_id) & (Balance.group_id == User.group_id))
        result = await session.execute(stmt)
        recipient_balance = result.scalars().first()

        if not recipient_balance:
            await message.edit_text("❌ Получатель не найден.")
            await state.clear()
            return

        # Обновляем балансы
        sender_balance.balance -= amount
        recipient_balance.balance += amount

        # Сохраняем изменения в базе данных
        await session.commit()

        await message.answer(f"✅ Успешно переведено {amount} юнитов пользователю {recipient_id}.")

        # Завершаем состояние
        await state.clear()

@router.callback_query(F.data == "back_to_balance")
async def back_to_balance(callback_query: CallbackQuery, state: FSMContext):
    """
    Обработчик для кнопки "Назад".
    Возвращает пользователя к меню баланса в том же сообщении.
    """
    await state.clear()  # Очищаем состояние

    # Создаем inline-кнопки для меню баланса
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Посмотреть баланс", callback_data="view_balance")],
        [InlineKeyboardButton(text="Перевести юниты", callback_data="transfer_units")]
    ])

    # Редактируем текущее сообщение
    await callback_query.message.edit_text(
        text="Что требуется сделать?",
        reply_markup=keyboard
    )