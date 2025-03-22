# Основные импорты aiogram
from aiogram import Router, F, Bot
from aiogram.types import (
    Message
)
from aiogram.filters import Command

# Импорты для работы с базой данных
from sqlalchemy import select
from db.database import async_session
from db.models import Group, User, Balance

router = Router()

@router.message(Command("group_info"))
async def group_info(message: Message, bot: Bot):
    from sprint_results import get_sprint_end_date
    user_id = message.from_user.id

    async with async_session() as session:
        # Получаем пользователя из базы
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user or not user.group_id:
            await message.answer("❌ Ты не состоишь в группе.")
            return

        group_id = user.group_id

        # Получаем информацию о группе
        stmt = select(Group).where(Group.id == group_id)
        result = await session.execute(stmt)
        group = result.scalars().first()

        if not group:
            await message.answer("❌ Группа не найдена.")
            return

        # Получаем список участников группы с балансом
        stmt = (
            select(User.id, Group.name, Balance.balance)
            .join(Group, Group.id == User.group_id)
            .join(Balance, (Balance.user_id == User.id) & (Balance.group_id == User.group_id))
            .where(User.group_id == group_id)
        )
        result = await session.execute(stmt)
        members = result.all()

        members_info = []
        for m in members:
            try:
                chat_member = await bot.get_chat(m[0])  # Запрос в Telegram API
                tg_name = chat_member.first_name  # Берем имя из Telegram

                members_info.append(
                    f"👤 {tg_name} | ID: {m[0]} | Нагрузка: {group.weights.get(str(m[0]), 0):.0f}% {'(👑 Владелец)' if m[0] == group.owner_id else ''}| баланс {m[2]}"
                )
            except Exception as e:
                print(f"Ошибка при получении данных пользователя {m[0]}: {e}")

        members_text = "\n".join(members_info) if members_info else "Пока нет участников."

        # Формируем ответ
        response = (
            f"📚 Информация о группе:\n\n"
            f"Название: {group.name}\n"
            f"День начала спринта: {group.start_day}\n"
            f"Длительность спринта: {group.sprint_duration} дней\n"
            f"День окончания текщего спринта: {get_sprint_end_date(group.start_day, group.sprint_duration)} 00:00\n\n"
            f"Баланс группы: {group.group_balance}\n\n"
            f"👥 Участники:\n\n{members_text}\n"
        )

        await message.answer(response)