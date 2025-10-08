"""
database.py — конфигурация базы данных и сессий SQLAlchemy
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

# URL базы данных (по умолчанию SQLite)
DATABASE_URL = os.getenv("DB_URL", "sqlite:///./meetings.db")

# Создание движка подключения
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Создание фабрики сессий
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Базовый класс для всех моделей
Base = declarative_base()
