# app/keyboards/user.py - ПОЛНАЯ ВЕРСИЯ

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.callbacks import CB


def categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=cat, callback_data=f"{CB.CATEGORY}:{cat}")]
        for cat in categories
    ]

    # Кнопка корзины
    buttons.append([
        InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products, category_name: str, show_unavailable: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура товаров с указанием доступности"""
    buttons = []

    for p in products:
        # Определяем emoji доступности
        if p.available and p.stock_grams > 0:
            emoji = "✅"
            qty_info = f" ({p.stock_grams}г)" if p.stock_grams < 1000 else ""
            callback_data = f"{CB.PRODUCT}:{p.id}:{category_name}"
        else:
            emoji = "❌"
            qty_info = " (нет в наличии)"
            callback_data = f"product:unavailable:{p.id}"

        button_text = f"{emoji} {p.name} — {int(p.price)} RSD{qty_info}"

        button = InlineKeyboardButton(
            text=button_text,
            callback_data=callback_data
        )
        buttons.append([button])

    # Кнопка "Назад к категориям"
    buttons.append([
        InlineKeyboardButton(
            text="⬅ Назад к категориям",
            callback_data="back_to_categories"
        )
    ])

    # Кнопка корзины
    buttons.append([
        InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quantity_keyboard(product_id: int, category: str, price: float, qty: int = 1):
    total = int(price * qty)

    buttons = [
        [
            InlineKeyboardButton(
                text="−",
                callback_data=f"{CB.QTY}:{product_id}:dec:{category}:{qty}"
            ),
            InlineKeyboardButton(
                text=str(qty),
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text="+",
                callback_data=f"{CB.QTY}:{product_id}:inc:{category}:{qty}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Добавить в корзину ({total} RSD)",
                callback_data=f"{CB.CART_ADD}:{product_id}:{qty}:{category}"
            )
        ],
        [  # Кнопка "Назад к товарам категории"
            InlineKeyboardButton(
                text="⬅ Назад к товарам",
                callback_data=f"{CB.CATEGORY}:{category}"
            )
        ],
        [  # Кнопка "Назад к категориям"
            InlineKeyboardButton(
                text="📂 Назад к категориям",
                callback_data="back_to_categories"
            )
        ],
        [  # Кнопка корзины
            InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_keyboard():
    """Основная клавиатура корзины"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data=CB.CART_CLEAR
            ),
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data=CB.CART_SHOW
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Проверить наличие",
                callback_data="cart:check_availability"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=CB.ORDER_CONFIRM
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CB.ORDER_CANCEL
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_cart_keyboard():
    """Клавиатура для возврата в корзину после отмены заказа"""
    buttons = [
        [InlineKeyboardButton(text="🛒 Вернуться в корзину", callback_data="show_cart")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_categories")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_item_management_keyboard(product_id: int, current_qty: int, max_qty: int):
    """Клавиатура для управления конкретным товаром в корзине"""
    # Предлагаем варианты количества
    suggested_quantities = []

    # Стандартные шаги (в граммах)
    steps = [100, 250, 500, 1000]

    for step in steps:
        if step <= max_qty:
            suggested_quantities.append(
                InlineKeyboardButton(
                    text=f"{step}г",
                    callback_data=f"cart:update:{product_id}:{step}"
                )
            )

    # Кнопки +/- для точной настройки
    adjust_buttons = []

    if current_qty > 100:
        adjust_buttons.append(
            InlineKeyboardButton(
                text="-100г",
                callback_data=f"cart:update:{product_id}:{current_qty - 100}"
            )
        )

    adjust_buttons.append(
        InlineKeyboardButton(
            text=f"Текущее: {current_qty}г",
            callback_data="noop"
        )
    )

    if current_qty + 100 <= max_qty:
        adjust_buttons.append(
            InlineKeyboardButton(
                text="+100г",
                callback_data=f"cart:update:{product_id}:{current_qty + 100}"
            )
        )

    # Основные кнопки управления
    buttons = []

    if suggested_quantities:
        # Разбиваем на ряды по 2 кнопки
        for i in range(0, len(suggested_quantities), 2):
            row = suggested_quantities[i:i + 2]
            buttons.append(row)

    if adjust_buttons:
        buttons.append(adjust_buttons)

    # Кнопки удаления и назад
    buttons.append([
        InlineKeyboardButton(
            text="🗑 Удалить из корзину",
            callback_data=f"cart:remove:{product_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(text="🔙 В корзину", callback_data="show_cart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
    # Кнопка корзины
    buttons.append([
        InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def quantity_keyboard(product_id: int, category: str, price: float, qty: int = 1):
    total = int(price * qty)

    buttons = [
        [
            InlineKeyboardButton(
                text="−",
                callback_data=f"{CB.QTY}:{product_id}:dec:{category}:{qty}"
            ),
            InlineKeyboardButton(
                text=str(qty),
                callback_data="noop"
            ),
            InlineKeyboardButton(
                text="+",
                callback_data=f"{CB.QTY}:{product_id}:inc:{category}:{qty}"
            )
        ],
        [
            InlineKeyboardButton(
                text=f"Добавить в корзину ({total} RSD)",
                callback_data=f"{CB.CART_ADD}:{product_id}:{qty}:{category}"
            )
        ],
        [  # Кнопка "Назад к товарам категории"
            InlineKeyboardButton(
                text="⬅ Назад к товарам",
                callback_data=f"{CB.CATEGORY}:{category}"
            )
        ],
        [  # Кнопка "Назад к категориям"
            InlineKeyboardButton(
                text="📂 Назад к категориям",
                callback_data="back_to_categories"
            )
        ],
        [  # Кнопка корзины
            InlineKeyboardButton(text="🛒 Корзина", callback_data="show_cart")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_keyboard():
    """Основная клавиатура корзины"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🗑 Очистить корзину",
                callback_data=CB.CART_CLEAR
            ),
            InlineKeyboardButton(
                text="✅ Оформить заказ",
                callback_data=CB.CART_SHOW
            )
        ],
        [
            InlineKeyboardButton(
                text="🔄 Проверить наличие",
                callback_data="cart:check_availability"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_keyboard():
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=CB.ORDER_CONFIRM
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=CB.ORDER_CANCEL
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_cart_keyboard():
    """Клавиатура для возврата в корзину после отмены заказа"""
    buttons = [
        [InlineKeyboardButton(text="🛒 Вернуться в корзину", callback_data="show_cart")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="back_to_categories")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cart_item_management_keyboard(product_id: int, current_qty: int, max_qty: int):
    """Клавиатура для управления конкретным товаром в корзине"""
    # Предлагаем варианты количества
    suggested_quantities = []

    # Стандартные шаги (в граммах)
    steps = [100, 250, 500, 1000]

    for step in steps:
        if step <= max_qty:
            suggested_quantities.append(
                InlineKeyboardButton(
                    text=f"{step}г",
                    callback_data=f"cart:update:{product_id}:{step}"
                )
            )

    # Кнопки +/- для точной настройки
    adjust_buttons = []

    if current_qty > 100:
        adjust_buttons.append(
            InlineKeyboardButton(
                text="-100г",
                callback_data=f"cart:update:{product_id}:{current_qty - 100}"
            )
        )

    adjust_buttons.append(
        InlineKeyboardButton(
            text=f"Текущее: {current_qty}г",
            callback_data="noop"
        )
    )

    if current_qty + 100 <= max_qty:
        adjust_buttons.append(
            InlineKeyboardButton(
                text="+100г",
                callback_data=f"cart:update:{product_id}:{current_qty + 100}"
            )
        )

    # Основные кнопки управления
    buttons = []

    if suggested_quantities:
        # Разбиваем на ряды по 2 кнопки
        for i in range(0, len(suggested_quantities), 2):
            row = suggested_quantities[i:i + 2]
            buttons.append(row)

    if adjust_buttons:
        buttons.append(adjust_buttons)

    # Кнопки удаления и назад
    buttons.append([
        InlineKeyboardButton(
            text="🗑 Удалить из корзины",
            callback_data=f"cart:remove:{product_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(text="🔙 В корзину", callback_data="show_cart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)