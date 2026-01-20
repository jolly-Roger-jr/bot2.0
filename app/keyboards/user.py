# app/keyboards/user.py - ПОЛНЫЙ ФАЙЛ С КНОПКАМИ +/- 100г
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def categories_keyboard(categories: list[str], user_id: int = None, cart_info: dict = None) -> InlineKeyboardMarkup:
    """Клавиатура с категориями товаров и кнопкой корзины"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.button(
            text=f"📦 {category}",
            callback_data=f"category:{category}"
        )

    # Добавляем кнопку корзины, если передан user_id и есть информация о корзине
    if user_id and cart_info:
        if cart_info.get('has_items', False):
            cart_text = f"🛒 Корзина ({cart_info['items_count']}) - {int(cart_info['total'])} RSD"
        else:
            cart_text = "🛒 Корзина (пуста)"

        builder.button(
            text=cart_text,
            callback_data="show_cart"
        )
    elif user_id:
        # Если нет информации о корзине, показываем простую кнопку
        builder.button(
            text="🛒 Корзина",
            callback_data="show_cart"
        )

    builder.adjust(1)
    return builder.as_markup()


def products_keyboard(products, category: str, show_unavailable: bool = False,
                      user_id: int = None, cart_info: dict = None) -> InlineKeyboardMarkup:
    """Клавиатура с товарами категории и кнопкой корзины"""
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

    # Добавляем кнопку корзины
    if user_id and cart_info:
        if cart_info.get('has_items', False):
            cart_text = f"🛒 Корзина ({cart_info['items_count']}) - {int(cart_info['total'])} RSD"
        else:
            cart_text = "🛒 Корзина (пуста)"

        builder.button(
            text=cart_text,
            callback_data="show_cart"
        )
    elif user_id:
        builder.button(
            text="🛒 Корзина",
            callback_data="show_cart"
        )

    builder.adjust(1)
    return builder.as_markup()


def quantity_keyboard(product_id: int, category: str, price: float, current_qty: int = 100) -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества товара с шагом 100г"""
    builder = InlineKeyboardBuilder()

    # Кнопки изменения количества с шагом 100г
    builder.button(
        text="➖100г",
        callback_data=f"qty:{product_id}:dec_100:{category}:{current_qty}"
    )

    builder.button(
        text=f"{current_qty}г",
        callback_data="noop"
    )

    builder.button(
        text="➕100г",
        callback_data=f"qty:{product_id}:inc_100:{category}:{current_qty}"
    )

    # Кнопка добавления в корзину
    builder.button(
        text=f"🛒 Добавить ({price * current_qty / 100:.0f} RSD)",
        callback_data=f"cart:add:{product_id}:{current_qty}:{category}"
    )

    # Кнопка назад к товарам категории
    builder.button(
        text="🔙 Назад",
        callback_data=f"category:{category}"
    )

    builder.adjust(3, 1, 1)
    return builder.as_markup()


def product_card_keyboard(product_id: int, category: str, price: float,
                          current_cart_qty: int = 0) -> InlineKeyboardMarkup:
    """Клавиатура для карточки товара (альтернативный вариант)"""
    builder = InlineKeyboardBuilder()

    if current_cart_qty > 0:
        # Если товар уже в корзине, показываем текущее количество
        builder.button(
            text=f"В корзине: {current_cart_qty}г",
            callback_data="noop"
        )

        builder.adjust(1)
    else:
        # Если товара нет в корзине, показываем кнопку добавления 100г
        builder.button(
            text=f"🛒 Добавить 100г ({price} RSD)",
            callback_data=f"cart:add_100g:{product_id}:{category}"
        )

        builder.adjust(1)

    # Кнопка назад к товарам категории
    builder.button(
        text="🔙 Назад",
        callback_data=f"category:{category}"
    )

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
    """Клавиатура управления товаром в корзине с шагом 100г"""
    buttons = []

    # Проверяем, чтобы не было отрицательных значений
    safe_current_qty = max(100, current_qty)  # Минимум 100г

    # Кнопки изменения количества (шаг 100г)
    buttons.append([
        InlineKeyboardButton(text="➖100г", callback_data=f"cart:update:{product_id}:{safe_current_qty - 100}"),
        InlineKeyboardButton(text=f"{safe_current_qty}г", callback_data="noop"),
        InlineKeyboardButton(text="➕100г", callback_data=f"cart:update:{product_id}:{safe_current_qty + 100}")
    ])

    # Кнопка удаления
    buttons.append([
        InlineKeyboardButton(text="🗑 Удалить из корзины", callback_data=f"cart:remove:{product_id}")
    ])

    # Кнопка назад
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад в корзину", callback_data="show_cart")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


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


def get_cart_button(cart_info: dict = None) -> list[list[InlineKeyboardButton]]:
    """
    Получить кнопку корзины как отдельный элемент для вставки в другие клавиатуры
    """
    if cart_info and cart_info.get('has_items', False):
        text = f"🛒 Корзина ({cart_info['items_count']}) - {int(cart_info['total'])} RSD"
    else:
        text = "🛒 Корзина"

    return [[InlineKeyboardButton(text=text, callback_data="show_cart")]]