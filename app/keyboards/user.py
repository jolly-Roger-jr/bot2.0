from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def categories_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🍖 Лакомства",
                    callback_data="category_treats"
                )
            ]
        ]
    )

def categories_keyboard(categories):
    buttons = [
        [InlineKeyboardButton(text=f"🦴 {c.name}", callback_data=f"cat_{c.id}")]
        for c in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def product_cart_keyboard(product_id, grams):
    if grams < 100:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{product_id}")]
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➖", callback_data=f"dec_{product_id}"),
                InlineKeyboardButton(text=f"{grams} г", callback_data="noop"),
                InlineKeyboardButton(text="➕", callback_data=f"add_{product_id}")
            ],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")]
        ]
    )

def cart_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Очистить", callback_data="cart_clear")],
            [InlineKeyboardButton(text="🛎️ Оформить заказ", callback_data="order")]
        ]
    )