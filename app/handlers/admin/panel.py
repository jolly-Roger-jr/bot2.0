from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.config import ADMIN_ID
from app.keyboards.admin import admin_menu

router = Router()

@router.message(F.text == "/admin")
async def admin_entry(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ Админ-панель Barkery", reply_markup=admin_menu())