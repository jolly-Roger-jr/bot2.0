# app/db/engine.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# ✅ ТОЛЬКО НАСТРОЙКИ ИЗ .env, НИКАКИХ ХАРДКОДОВ
engine = create_async_engine(settings.database_url, echo=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass