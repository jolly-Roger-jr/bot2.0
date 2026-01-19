# app/keyboards/admin.py - КАНОНИЧНАЯ ВЕРСИЯ
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu():
    """Главное меню админки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Товары", callback_data="admin:products"),
                InlineKeyboardButton(text="📊 Остатки", callback_data="admin:stock")
            ],
            [
                InlineKeyboardButton(text="🛒 Заказы", callback_data="admin:orders"),
                InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:add_product")
            ],
            [
                InlineKeyboardButton(text="📂 Добавить категорию", callback_data="admin_add_category")
            ]
        ]
    )


def back_to_admin_menu():
    """Кнопка возврата в админ-меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin:back")]
        ]
    )