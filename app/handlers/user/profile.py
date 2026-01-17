from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models import User

router = Router()

@router.message(lambda m: m.text and m.text.startswith("+"))
async def save_phone(message: Message):
    async for session in get_session():
        user = (await session.execute(
            select(User).where(User.tg_id == message.from_user.id)
        )).scalar_one_or_none()

        if not user:
            user = User(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                phone=message.text
            )
            session.add(user)
        else:
            user.phone = message.text

        await session.commit()

    await message.answer("✅ Спасибо! Номер сохранён 🐾")