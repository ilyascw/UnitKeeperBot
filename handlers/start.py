from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.database import get_db  # Импортируем функцию получения сессии
from db.models import User  # Импортируем модель пользователя
import logging
import asyncio

router = Router()

@router.message(Command("start"))
async def start_handler(message: Message):
    """
    Обработчик команды /start.
    Если пользователя нет в базе — создаёт запись и предлагает создать/вступить в группу.
    Если пользователь есть, но не состоит в группе — предлагает создать/вступить.
    Если уже состоит в группе — заглушка.
    """
    user_id = message.from_user.id

    async for db in get_db():
        # Проверяем, есть ли пользователь в БД
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()

        if user is None:
            # Добавляем нового пользователя в БД
            new_user = User(id=user_id, group_id=None)
            db.add(new_user)
            await db.commit()

            # Отправляем кнопки
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="➕ Создать группу")],
                    [KeyboardButton(text="🔑 Вступить в группу")]
                ],
                resize_keyboard=True
            )
            await message.answer("Привет! Ты еще не зарегистрирован.\nВыбери действие:", reply_markup=keyboard)

        elif user.group_id is None:
            # Пользователь зарегистрирован, но без группы
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="➕ Создать группу")],
                    [KeyboardButton(text="🔑 Вступить в группу")]
                ],
                resize_keyboard=True
            )
            await message.answer("Ты не состоишь в группе. Выбери действие:", reply_markup=keyboard)

        else:
            # Пользователь уже в группе
            await message.answer("Ты уже в группе. Используй другие команды.")