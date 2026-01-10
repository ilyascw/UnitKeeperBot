# UnitKeeperBot

> **⚠️ Архитектурная ретроспектива (2026)**
>
> Данный проект был разработан на раннем этапе моего пути в бэкенд-разработке. Оглядываясь назад с высоты текущего опыта (Middle AI/Python Engineer), я выделяю ряд улучшений, которые являются стандартом для моих текущих решений:
>
> 1.  **Архитектура:** Вынос бизнес-логики из хендлеров в **Service Layer**. Текущая реализация (Logic in Handlers) допустима для MVP, но усложняет тестирование.
> 2.  **Работа с БД:** Внедрение паттерна **Repository** и **Unit of Work** вместо прямых вызовов ORM. Использование фабрики сессий и Dependency Injection.
> 3.  **Инфраструктура:** Контейнеризация через **Docker/Compose** (сейчас запуск локальный).
> 4.  **Конфиг:** Использование `pydantic-settings` вместо парсинга `.env` вручную.
>
> *Код оставлен в исходном виде ("as is") как пример продуктового мышления и умения доводить идеи до работающего инструмента.*

---

## 📋 О проекте

**UnitKeeperBot** — асинхронный Telegram-бот для управления домашними обязанностями (Chore Management) на основе модели юнит-экономики. Система позволяет оцифровать вклад участников быта, используя балльную систему оценки задач.

**Ключевая задача:** Устранение субъективности в оценке домашнего труда и прозрачная визуализация вклада каждого участника группы.

### Функциональные возможности
* **Unit Economy System:** Кастомизируемая оценка стоимости задач (в юнитах) и частоты их выполнения.
* **Групповое взаимодействие:** Создание закрытых групп, ролевая модель (Админ/Участник), инвайт-система по кодам доступа.
* **Data Import/Export:** Массовая загрузка задач через шаблоны Excel/CSV (реализовано на Pandas).
* **Sprint Cycles:** Автоматическое подведение итогов периода (спринта), расчет баланса и перераспределение нагрузки.
* **Transaction System:** Механизм трансфера юнитов между участниками (peer-to-peer).

## 🛠 Технический стек

* **Language:** Python 3.10+
* **Framework:** Aiogram 3.x (Asynchronous)
* **Database:** PostgreSQL + AsyncPG
* **ORM:** SQLAlchemy (Async)
* **Migrations:** Alembic
* **Data Processing:** Pandas, OpenPyXL

## 🚀 Установка и запуск

Проект предполагает локальный запуск (см. ретроспективу касательно Docker).

### 1. Клонирование и окружение
```bash
git clone [https://github.com/ilyascw/UnitKeeperBot.git](https://github.com/ilyascw/UnitKeeperBot.git)
cd UnitKeeperBot
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 2. Конфигурация

Создайте файл `.env` в корне проекта по образцу:

```ini
TOKEN=your_telegram_bot_token
# Формат: postgresql+asyncpg://user:password@host/dbname
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost/unitkeeper_db

```

### 3. База данных

Примените миграции (или инициализацию) для создания схемы:

```bash
# Если используется alembic
alembic upgrade head

# Или через встроенный скрипт инициализации (Legacy)
python db/init_db.py

```

### 4. Запуск

```bash
python bot.py

```

## 🗺 Roadmap (Архив)

Реализованные и запланированные фичи на момент активной разработки:

* [x] Базовая механика учета задач и баланса
* [x] Парсинг Excel-файлов
* [ ] Магазин бенефитов (обмен юнитов на вознаграждения)
* [ ] Интеграция с Google Calendar API

## 📄 Лицензия

Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
