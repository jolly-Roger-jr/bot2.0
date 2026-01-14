from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Товары", callback_data="admin_products")],
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")]
        ]
    )