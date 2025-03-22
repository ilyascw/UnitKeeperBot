from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, TIMESTAMP, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.ext.asyncio import create_async_engine
from config import DATABASE_URL

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    start_day = Column(String, nullable=False)
    sprint_duration = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    group_balance = Column(Numeric, default=0)
    weights = Column(JSON, default={})

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"))

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    title = Column(String, nullable=False)
    frequency = Column(Numeric, nullable=False)
    cost = Column(Numeric, nullable=False)
    status = Column(Boolean, default=True)  # True = активна, False = неактивна

class Log(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)

class Balance(Base):
    __tablename__ = "balances"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    balance = Column(Numeric, default=0)

# Здесь создаём асинхронный движок и сессию
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаём все таблицы в базе данных
async def create_tables():
    async with engine.begin() as conn:
        # Здесь создаются все таблицы, которые описаны в Base
        await conn.run_sync(Base.metadata.create_all)

# Вызываем создание таблиц
import asyncio
asyncio.run(create_tables())