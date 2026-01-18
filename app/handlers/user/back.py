# app/handlers/user/back.py

from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.services import catalog
from app.keyboards.user import categories_keyboard

router = Router()


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    categories = await catalog.get_categories()

    await callback.message.edit_text(
        "🐶 Barkery Shop\nВыберите категорию:",
        reply_markup=categories_keyboard(categories)
    )
    await callback.answer()