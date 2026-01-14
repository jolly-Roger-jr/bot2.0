# app/keyboards/user.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services import catalog

def categories_keyboard():
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"category:{cat}")]
            for cat in catalog.get_categories()
        ]
    )
    return kb

def products_keyboard(category: str):
    products = catalog.get_products(category)
    if not products:
        return None
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p, callback_data=f"product:{p}")]
            for p in products
        ]
    )
    return kb