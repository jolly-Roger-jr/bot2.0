# app/handlers/user/profile.py - ИСПРАВЛЕННЫЙ

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select, update
from app.db.session import get_session
from app.db.models import Order  # Используем существующую модель вместо User

router = Router()


@router.message(F.text.startswith("+"))
async def save_phone(message: Message):
    """Сохранение телефона пользователя (привязка к последнему заказу)"""
    phone = message.text.strip()

    async for session in get_session():
        try:
            # Находим последний заказ пользователя без телефона
            result = await session.execute(
                select(Order)
                .where(
                    Order.user_id == str(message.from_user.id),
                    (Order.phone.is_(None) | (Order.phone == ""))
                )
                .order_by(Order.created_at.desc())
                .limit(1)
            )

            order = result.scalar_one_or_none()

            if order:
                # Обновляем телефон в заказе
                order.phone = phone
                await session.commit()
                await message.answer("✅ Номер телефона сохранён для вашего заказа! 🐾")
            else:
                await message.answer(
                    "📱 Номер телефона принят!\n\n"
                    "Мы сохраним его при оформлении следующего заказа. "
                    "Спасибо! 🐾"
                )

        except Exception as e:
            await session.rollback()
            await message.answer("❌ Произошла ошибка при сохранении номера.")
            print(f"Error saving phone: {e}")