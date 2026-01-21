# app/keyboards/user.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def center_text(text: str, width: int = 20) -> str:
    """Центрирование текста с помощью пробелов-заполнителей"""
    spaces = " "  # Это специальный пробел, а не обычный

    if len(text) >= width:
        return text

    total_spaces = width - len(text)
    left_spaces = total_spaces // 2
    right_spaces = total_spaces - left_spaces

    return f"{spaces * left_spaces}{text}{spaces * right_spaces}"


def create_centered_button(text: str, callback_data: str) -> list:
    """Создает центрированную кнопку с заполнителями"""
    centered_text = center_text(f"    {text}    ", 25)
    return [InlineKeyboardButton(text=centered_text, callback_data=callback_data)]


def categories_keyboard(categories, user_id=None, cart_info=None):
    """Клавиатура категорий с центрированием"""
    keyboard = []

    dog_emojis = ["🐕", "🐩", "🦮", "🐕‍🦺", "🐶", "🧸"]

    for i, category in enumerate(categories):
        emoji = dog_emojis[i % len(dog_emojis)]
        keyboard.append(create_centered_button(f"{emoji} {category}", f"category:{category}"))

    keyboard.append([InlineKeyboardButton(text="              ", callback_data="noop")])

    if cart_info and cart_info.get('has_items', False):
        keyboard.append(create_centered_button(f"🛍️ Корзина ({cart_info['items_count']})", "show_cart"))
    else:
        keyboard.append(create_centered_button("🛍️ Корзина", "show_cart"))

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def product_detail_keyboard(product_id, category, price, in_cart_qty=0, stock_grams=0):
    """Карточка товара с центрированными кнопками +/-"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [  # СТРОКА 1: Кнопки +/- с заполнителями
                InlineKeyboardButton(
                    text="    ➖    ",
                    callback_data=f"qty:dec:{product_id}:{category}:{in_cart_qty}" if in_cart_qty > 0 else "noop"
                ),
                InlineKeyboardButton(
                    text=f" {in_cart_qty}г ",
                    callback_data="noop"
                ),
                InlineKeyboardButton(
                    text="    ➕    ",
                    callback_data=f"qty:inc:{product_id}:{category}:{in_cart_qty}"
                )
            ],
            create_centered_button(  # СТРОКА 2
                f"🛒 В корзину ({price * max(100, in_cart_qty) / 100:.0f} RSD)",
                f"cart:add:{product_id}:{max(100, in_cart_qty)}:{category}"
            ),
            create_centered_button("📦 К товарам", f"category:{category}")  # СТРОКА 3
        ]
    )


def cart_keyboard():
    """Клавиатура корзины"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            create_centered_button("✅ Оформить заказ", "cart:show"),
            create_centered_button("🗑️ Очистить корзину", "cart:clear"),
            [InlineKeyboardButton(text="              ", callback_data="noop")],
            create_centered_button("🏠 В категории", "back_to_categories")
        ]
    )


def update_quantity_keyboard(product_id, category, price, current_qty, stock_grams):
    """Клавиатура для изменения количества"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [  # СТРОКА 1
                InlineKeyboardButton(
                    text="    ➖    ",
                    callback_data=f"qty:dec:{product_id}:{category}:{current_qty}" if current_qty > 0 else "noop"
                ),
                InlineKeyboardButton(
                    text=f" {current_qty}г ",
                    callback_data="noop"
                ),
                InlineKeyboardButton(
                    text="    ➕    ",
                    callback_data=f"qty:inc:{product_id}:{category}:{current_qty}"
                )
            ],
            create_centered_button(  # СТРОКА 2
                f"🛒 В корзину ({price * max(100, current_qty) / 100:.0f} RSD)",
                f"cart:add:{product_id}:{max(100, current_qty)}:{category}"
            ),
            create_centered_button("🔙 Назад к товару", f"product_detail:{product_id}:{category}")
        ]
    )


def cart_item_management_keyboard(product_id, current_qty, stock_grams):
    """Управление товаром в корзине"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [  # СТРОКА 1
                InlineKeyboardButton(
                    text="    ➖    ",
                    callback_data=f"cart:update:{product_id}:{max(100, current_qty - 100)}"
                ),
                InlineKeyboardButton(
                    text=f" {current_qty}г ",
                    callback_data="noop"
                ),
                InlineKeyboardButton(
                    text="    ➕    ",
                    callback_data=f"cart:update:{product_id}:{current_qty + 100}"
                )
            ],
            create_centered_button("❌ Удалить", f"cart:remove:{product_id}"),
            [InlineKeyboardButton(text="              ", callback_data="noop")],
            create_centered_button("🛒 Назад в корзину", "show_cart")
        ]
    )


def confirm_keyboard():
    """Подтверждение заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            create_centered_button("✅ Подтвердить заказ", "order:confirm"),
            create_centered_button("❌ Отменить", "order:cancel")
        ]
    )


def order_success_keyboard():
    """Клавиатура после успешного оформления заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            create_centered_button("🏠 В главное меню", "main_menu"),
            create_centered_button("📦 Продолжить покупки", "catalog")
        ]
    )


def back_to_cart_keyboard():
    """Клавиатура для возврата в корзину"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            create_centered_button("🛒 Вернуться в корзину", "show_cart")
        ]
    )


def get_cart_button():
    """Кнопка корзины для меню"""
    return InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")


def products_keyboard(products, category, show_unavailable=False, user_id=None, cart_info=None):
    """Список товаров"""
    keyboard = []

    food_emojis = ["🍖", "🥩", "🦴", "🍗", "🥓", "🧀"]

    for i, product in enumerate(products):
        if product.available and product.stock_grams > 0:
            emoji = food_emojis[i % len(food_emojis)]
            keyboard.append(create_centered_button(
                f"{emoji} {product.name} - {product.price} RSD",
                f"product_detail:{product.id}:{category}"
            ))

    keyboard.append([InlineKeyboardButton(text="              ", callback_data="noop")])
    keyboard.append(create_centered_button("🏠 Назад к категориям", "back_to_categories"))

    if cart_info and cart_info.get('has_items', False):
        keyboard.append(create_centered_button(
            f"🛍️ Корзина ({cart_info['items_count']})",
            callback_data="show_cart"
        ))

    return InlineKeyboardMarkup(inline_keyboard=keyboard)