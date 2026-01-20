# app/db/session.py
from app.db.engine import SessionLocal


async def get_session():
    async with SessionLocal() as session:
        yield session