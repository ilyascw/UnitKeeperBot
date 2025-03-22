import os
import pandas as pd
from io import BytesIO
import asyncio
from aiogram import Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Bot
from db.database import async_session  # Импорт сессии БД
from db.models import Task, User, Group  # Модели для работы с БД

router = Router()

class AddTask(StatesGroup):
    wait_mode = State()  # Статус для выбора одного или нескольких
    wait_title = State()  # Статус для ввода названия задачи
    wait_frequency = State()  # Статус для ввода периодичности
    wait_cost = State()  # Статус для ввода стоимости
    wait_file = State()  # Статус для загрузки файла с задачами

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✅ Действие отменено.")

@router.message(Command("add_task"))
async def start_add_task(message: Message, state: FSMContext):
    """Начало добавления задачи"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Одна задача", callback_data="add_one_task")],
            [InlineKeyboardButton(text="Множество задач", callback_data="add_multiple_tasks")]
        ]
    )
    await message.answer("Вы хотите добавить одну задачу или несколько?", reply_markup=keyboard)
    await state.set_state(AddTask.wait_mode)

@router.callback_query(lambda query: query.data == "add_one_task")
async def add_one_task(callback_query: CallbackQuery, state: FSMContext):
    """Логика добавления одной задачи"""
    await callback_query.message.edit_text("Введите название задачи:")
    await state.set_state(AddTask.wait_title)

@router.callback_query(lambda query: query.data == "add_multiple_tasks")
async def add_multiple_tasks(callback_query: CallbackQuery, state: FSMContext):
    """Логика добавления нескольких задач"""
    # Путь к шаблону
    template_path = os.path.join(os.getcwd(), "templates", "task_template.xlsx")

    if os.path.exists(template_path):
        # Создаем объект InputFile
        file = FSInputFile(template_path)
        
        await callback_query.message.edit_text(
            "Отправьте файл с задачами в формате .xlsx или .csv. Пожалуйста, заполните шаблон и загрузите его."
            '\nПереодичность и стоимость - числа. переодичность должна быть целым числом.'
        )
        
        # Отправляем файл как шаблон
        await callback_query.message.answer_document(file, caption="Шаблон задач для загрузки.")
        await state.set_state(AddTask.wait_file)
    else:
        await callback_query.message.edit_text("❌ Шаблон не найден. Попробуйте снова позже.")

@router.message(AddTask.wait_title)
async def process_title(message: Message, state: FSMContext):
    """Запоминаем название задачи и запрашиваем периодичность"""
    await state.update_data(title=message.text)
    await message.answer("Введите периодичность выполнения (должно быть числом):")
    await state.set_state(AddTask.wait_frequency)

@router.message(AddTask.wait_frequency)
async def add_task_frequency(message: Message, state: FSMContext):
    """Запоминаем периодичность и запрашиваем стоимость"""
    try:
        frequency = int(message.text)
        await state.update_data(frequency=frequency)
        await message.answer("Введите стоимость задачи в юнитах:")
        await state.set_state(AddTask.wait_cost)
    except ValueError:
        await message.answer("❌ Периодичность должна быть числом. Пожалуйста, введите снова.")
        await state.set_state(AddTask.wait_frequency)

@router.message(AddTask.wait_cost)
async def add_task_cost(message: Message, state: FSMContext):
    """Сохраняем задачу в БД"""
    user_id = message.from_user.id
    data = await state.get_data()
    title = data["title"]
    frequency = data["frequency"]

    try:
        cost = int(message.text)
    except ValueError:
        await message.answer("❌ Стоимость должна быть числом. Пожалуйста, введите снова.")
        await state.set_state(AddTask.wait_cost)
        return

    # Получаем group_id пользователя
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user or not user.group_id:
            await message.answer("❌ Ошибка: ты не состоишь в группе.")
            return

        group_id = user.group_id  # Берем group_id пользователя

        # Добавляем задачу в базу данных
        task = Task(title=title, frequency=frequency, cost=cost, group_id=group_id)
        session.add(task)
        await session.commit()

    await message.answer(f"✅ Задача '{title}' добавлена в группу.")
    await state.clear()

@router.message(AddTask.wait_file)
async def process_file(message: Message, state: FSMContext, bot: Bot):
    """Обрабатываем загруженный файл с задачами без сохранения на диск"""
    if not message.document:
        await message.answer("❌ Ошибка: Пожалуйста, отправьте файл.")
        return

    file_id = message.document.file_id
    file = await bot.get_file(file_id)

    # Загружаем файл в память
    file_bytes = await bot.download(file)

    # Чтение файла и добавление задач в БД
    loop = asyncio.get_event_loop()
    tasks_to_add = await loop.run_in_executor(None, read_and_parse_file, file_bytes)

    if not tasks_to_add:
        await message.answer("❌ Ошибка: Некорректный формат файла.")
        return

    # Добавляем задачи в базу данных
    async with async_session() as session:
        # Получаем пользователя
        user = await session.get(User, message.from_user.id)

        if not user:  # Проверяем, найден ли пользователь
            await message.answer("❌ Ошибка: Пользователь не найден в базе.")
            return

        # Добавляем задачи в базу данных без вложенной транзакции
        for task_data in tasks_to_add:
            task = Task(**task_data, group_id=user.group_id)
            session.add(task)  # Добавляем задачу

        await session.commit()  # Является коммитом для всех операций в контексте сессии

    await message.answer(f"✅ {len(tasks_to_add)} задач(и) добавлены.")
    await state.clear()

def read_and_parse_file(file_bytes):
    """Функция для синхронного чтения и парсинга файла из памяти"""
    try:
        df = pd.read_excel(BytesIO(file_bytes.read()), engine="openpyxl")  # Читаем файл из памяти
        if not all(col in df.columns for col in ["Название", "Периодичность", "Стоимость"]):
            return None
        
        tasks_to_add = []
        for index, row in df.iterrows():
                # Проверка, что значения в колонках "Периодичность" и "Стоимость" являются числами
                if not (isinstance(row["Периодичность"], (int, float)) or not (isinstance(row["Стоимость"], (int, float)))):
                    print(f"Ошибка: Неверный тип данных на строке {index + 1}. Ожидаются числовые значения для 'Периодичность' и 'Стоимость'.")
                    return None

                # Проверка, что "Периодичность" является целым числом
                if not float(row["Периодичность"]).is_integer():
                    print(f"Ошибка: Неверное значение на строке {index + 1}. Периодичность должна быть целым числом.")
                    return None

        tasks_to_add = []
        for _, row in df.iterrows():
            task = {
                "title": row["Название"],
                "frequency": row["Периодичность"],
                "cost": row["Стоимость"]
            }
            tasks_to_add.append(task)

        return tasks_to_add
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")
        return None