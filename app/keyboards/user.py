# app/keyboards/user.py - КАНОНИЧНАЯ ВЕРСИЯ (исправленная)
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(
            text=f"📦 {category}",
            callback_data=f"category:{category}"
        )

    builder.adjust(1)
    return builder.as_markup()


def quantity_keyboard(product_id: int, category: str, price: float, qty: int = 100) -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества товара"""
    builder = InlineKeyboardBuilder()

    # Кнопки изменения количества
    builder.button(
        text="➖",
        callback_data=f"qty:{product_id}:dec:{category}:{qty}"
    )

    builder.button(
        text=f"{qty}г",
        callback_data="noop"
    )

    builder.button(
        text="➕",
        callback_data=f"qty:{product_id}:inc:{category}:{qty}"
    )

    # Кнопка добавления в корзину
    builder.button(
        text=f"🛒 Добавить ({price * qty / 100:.0f} RSD)",
        callback_data=f"cart:add:{product_id}:{qty}:{category}"
    )

    # Кнопка назад
    builder.button(
        text="🔙 Назад",
        callback_data=f"category:{category}"
    )

    builder.adjust(3, 1, 1)
    return builder.as_markup()


def products_keyboard(products, category: str, show_unavailable: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура с товарами категории"""
    builder = InlineKeyboardBuilder()

    for product in products:
        if product.available and product.stock_grams > 0:
            # Доступные товары
            builder.button(
                text=f"✅ {product.name} - {product.price} RSD/100г",
                callback_data=f"product:{product.id}:{category}"
            )
        elif show_unavailable:
            # Недоступные товары (только если show_unavailable=True)
            builder.button(
                text=f"❌ {product.name} - {product.price} RSD/100г",
                callback_data=f"product:unavailable:{product.id}"
            )

    # Кнопка назад к категориям
    builder.button(
        text="🔙 Назад к категориям",
        callback_data="back_to_categories"
    )

    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Очистить корзину", callback_data="cart:clear"),
                InlineKeyboardButton(text="✅ Оформить заказ", callback_data="cart:show")
            ],
            [
                InlineKeyboardButton(text="🔍 Проверить наличие", callback_data="cart:check_availability")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в каталог", callback_data="back_to_categories")
            ]
        ]
    )


def cart_item_management_keyboard(product_id: int, current_qty: int, max_qty: int) -> InlineKeyboardMarkup:
    """Клавиатура для управления конкретным товаром в корзине"""
    builder = InlineKeyboardBuilder()

    # Кнопки изменения количества
    builder.button(
        text="➖ 100г",
        callback_data=f"cart:update:{product_id}:{max(current_qty - 100, 100)}"
    )

    builder.button(
        text=f"{current_qty}г",
        callback_data="noop"
    )

    builder.button(
        text="➕ 100г",
        callback_data=f"cart:update:{product_id}:{min(current_qty + 100, max_qty)}"
    )

    # Кнопка удаления
    builder.button(
        text="🗑 Удалить из корзины",
        callback_data=f"cart:remove:{product_id}"
    )

    # Кнопка назад
    builder.button(
        text="🔙 Назад в корзину",
        callback_data="show_cart"
    )

    builder.adjust(3, 1, 1)
    return builder.as_markup()


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order:confirm"),
                InlineKeyboardButton(text="❌ Отменить", callback_data="order:cancel")
            ]
        ]
    )


def back_to_cart_keyboard() -> InlineKeyboardMarkup:
    """Кнопка возврата в корзину"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться в корзину", callback_data="show_cart")]
        ]
    )