from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import asyncio
import sys
import os

# Добавляем родительскую директорию в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import DATABASE_URL

Base = declarative_base()  # Создаём базовый класс для моделей

# Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,        
    pool_size=5,      
    max_overflow=10   
)

# Фабрика сессий (удаляем старый SessionLocal)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# Функция получения сессии
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()  
        except Exception as e:
            await session.rollback()  
            print(f"Ошибка работы с БД: {e}")
        finally:
            await session.close()  

# Тест соединения с БД
async def test_db():
    async for session in get_db():
        if isinstance(session, AsyncSession):
            print("✅ Подключение к БД работает!")
        else:
            print("❌ Ошибка подключения к БД!")

asyncio.run(test_db())