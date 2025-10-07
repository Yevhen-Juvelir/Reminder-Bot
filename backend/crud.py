from sqlalchemy.orm import Session
from backend.models import User, Event
from datetime import datetime

def get_user(db: Session, telegram_id: int):
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int, username: str, phone: str = None):
    user = User(telegram_id=telegram_id, username=username, phone=phone)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_event(db: Session, user_id: int, title: str, description: str | None, time: datetime):
    event = Event(user_id=user_id, title=title, description=description, time=time)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def get_upcoming_events(db: Session, now: datetime):
    return db.query(Event).filter(Event.time <= now).all()
