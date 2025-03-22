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
    echo=False,        
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
        finally:
            await session.close()  
