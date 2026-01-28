"""
Reply клавиатуры для бота (постоянные кнопки под полем ввода)
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главная Reply клавиатура"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📦 Каталог"),
                KeyboardButton(text="🛒 Корзина")
            ],
            [
                KeyboardButton(text="👤 Профиль"),
                KeyboardButton(text="❓ Помощь")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard


def get_catalog_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура для каталога"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⬅️ Назад"),
                KeyboardButton(text="🛒 Корзина")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите категорию..."
    )
    return keyboard


def get_cart_reply_keyboard() -> ReplyKeyboardMarkup:
    """Reply клавиатура для корзины"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🛎️ Оформить"),
                KeyboardButton(text="❌ Очистить")
            ],
            [
                KeyboardButton(text="⬅️ Главная"),
                KeyboardButton(text="📦 Каталог")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Управление корзиной..."
    )
    return keyboard


def get_back_only_keyboard() -> ReplyKeyboardMarkup:
    """Только кнопка Назад"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard


def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаление клавиатуры"""
    return ReplyKeyboardRemove()
