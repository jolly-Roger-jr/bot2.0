# app/handlers/admin/__init__.py - МИНИМАЛЬНЫЙ ФИКС
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("admin"))
async def admin_command(message: Message):
    from app.config import settings
    if message.from_user.id != settings.admin_id:
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    from app.keyboards.admin import admin_menu
    await message.answer("⚙️ Админ-панель Barkery", reply_markup=admin_menu())


# Убраны все setup функции - хендлеры подключаются напрямую в bot_canonical.py
__all__ = ['router']