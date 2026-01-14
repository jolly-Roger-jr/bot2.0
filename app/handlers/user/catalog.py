# app/handlers/user/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.keyboards.user import products_keyboard
from app.handlers.user.constants import NO_PRODUCTS_TEXT

router = Router()

@router.callback_query(F.data.startswith("category:"))
async def category_callback(query: CallbackQuery):
    category = query.data.split(":", 1)[1]
    kb = products_keyboard(category)
    if not kb:
        await query.answer(NO_PRODUCTS_TEXT)
        return
    await query.message.edit_text(f"Товары в категории {category}:", reply_markup=kb)

@router.callback_query(F.data.startswith("product:"))
async def product_callback(query: CallbackQuery):
    product = query.data.split(":", 1)[1]
    await query.answer(f"Вы выбрали товар: {product}")