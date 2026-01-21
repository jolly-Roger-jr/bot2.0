# app/db/engine.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Для тестов используем in-memory базу
if os.environ.get("TESTING") == "1":
    database_url = "sqlite+aiosqlite:///:memory:"
else:
    database_url = settings.database_url

engine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass