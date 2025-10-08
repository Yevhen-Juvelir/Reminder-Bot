"""
models.py — ORM-модели User и Event
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# Модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    full_name = Column(String)
    phone = Column(String)
    is_admin = Column(Boolean, default=False)

    # Один пользователь может иметь несколько событий
    events = relationship("Event", back_populates="user")


# Модель события
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    image_url = Column(String)
    time = Column(DateTime, nullable=False)

    # Обратная связь с пользователем
    user = relationship("User", back_populates="events")
