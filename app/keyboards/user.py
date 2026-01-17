from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from app.callbacks import CB


def categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"{CB.CATEGORY}:{cat}")]
            for cat in categories
        ]
    )


def products_keyboard(products, category_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{p.name} — {int(p.price)} RSD",
                    callback_data=f"{CB.PRODUCT}:{p.id}:{category_name}"
                )
            ]
            for p in products
        ]
    )


def quantity_keyboard(product_id: int, category: str, price: float, qty: int = 1):
    total = int(price * qty)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("−", callback_data=f"{CB.QTY}:{product_id}:dec:{category}"),
                InlineKeyboardButton(str(qty), callback_data="noop"),
                InlineKeyboardButton("+", callback_data=f"{CB.QTY}:{product_id}:inc:{category}")
            ],
            [
                InlineKeyboardButton(
                    f"Добавить в корзину ({total} RSD)",
                    callback_data=f"{CB.CART_ADD}:{product_id}:{qty}:{category}"
                )
            ],
            [
                InlineKeyboardButton("⬅ Назад", callback_data=f"{CB.CATEGORY}:{category}")
            ]
        ]
    )


def cart_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("🗑 Очистить корзину", callback_data=CB.CART_CLEAR),
                InlineKeyboardButton("✅ Оформить заказ", callback_data=CB.ORDER_CONFIRM)
            ]
        ]
    )