# app/keyboards/admin.py - ДОПОЛНЕННАЯ ВЕРСИЯ
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
                InlineKeyboardButton(text="📂 Добавить категорию", callback_data="admin:add_category")  # ✅ ИСПРАВЛЕНО
            ]
        ]
    )


def stock_management_menu():
    """Меню управления остатками товаров"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Просмотреть остатки", callback_data="stock:view")],
            [InlineKeyboardButton(text="➕ Добавить остатки", callback_data="stock:add")],
            [InlineKeyboardButton(text="📝 Изменить остатки", callback_data="stock:edit")],
            [InlineKeyboardButton(text="⚠️ Низкие остатки", callback_data="stock:low")],
            [InlineKeyboardButton(text="❌ Нет в наличии", callback_data="stock:out")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back")]
        ]
    )


def back_to_admin_menu():
    """Кнопка возврата в админ-меню"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin:back")]
        ]
    )