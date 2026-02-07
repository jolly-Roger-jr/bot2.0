# keyboards_smi.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📦 Каталог", callback_data="smi_catalog")
    )

    builder.row(
        InlineKeyboardButton(text="🛒 Корзина", callback_data="smi_cart"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="smi_profile")
    )

    builder.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="smi_help")
    )

    return builder.as_markup()


def categories_keyboard_smi(categories: list) -> InlineKeyboardMarkup:
    """Категории"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {category['name']}",
                callback_data=f"smi_category:{category['id']}"
            )
        )

    # Гипоаллергенные товары
    builder.row(
        InlineKeyboardButton(
            text="🥕🐟 Гипоаллергенные 🐏🎃",
            callback_data="smi_category:999"
        )
    )

    builder.row(
        InlineKeyboardButton(text="⬅️ Главная", callback_data="smi_main"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="smi_cart")
    )

    return builder.as_markup()


def products_keyboard_smi(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Товары категории"""
    builder = InlineKeyboardBuilder()

    for product in products:
        status = "✅" if product['available'] and product['stock_grams'] > 0 else "⏳"

        # Определяем отображение цены
        unit_type = product.get('unit_type', 'grams')
        if unit_type == 'grams':
            price_text = f"{product['price']} RSD/100г"
        else:
            price_text = f"{product['price']} RSD/шт"

        builder.row(
            InlineKeyboardButton(
                text=f"{status} {product['name']} - {price_text}",
                callback_data=f"smi_product:{product['id']}:{category_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="smi_catalog"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="smi_cart")
    )

    return builder.as_markup()


def product_card_keyboard_smi(
        product_id: int,
        category_id: int,
        current_qty: int = 0,
        unit_type: str = 'grams',
        measurement_step: int = 100
) -> InlineKeyboardMarkup:
    """Карточка товара"""
    builder = InlineKeyboardBuilder()

    # Определяем единицы
    if unit_type == 'grams':
        unit_symbol = 'г'
        step_symbol = f'{measurement_step}г'
    else:
        unit_symbol = 'шт'
        step_symbol = f'{measurement_step}шт'

    # Ряд 1: Управление количеством
    builder.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"smi_qty_dec:{product_id}:{category_id}"
        ),
        InlineKeyboardButton(
            text=f"{current_qty}{unit_symbol}",
            callback_data="smi_qty_info"
        ),
        InlineKeyboardButton(
            text="➕",
            callback_data=f"smi_qty_inc:{product_id}:{category_id}"
        )
    )

    # Ряд 2: Добавить в корзину
    if current_qty > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"🛒 Добавить ({current_qty}{unit_symbol})",
                callback_data=f"smi_cart_add:{product_id}:{current_qty}:{category_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="ℹ️ Выберите количество",
                callback_data="smi_qty_info"
            )
        )

    # Ряд 3: Навигация
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"smi_back_products:{category_id}"
        ),
        InlineKeyboardButton(
            text="🛒 Корзина",
            callback_data="smi_cart"
        ),
        InlineKeyboardButton(
            text="🏠 Главная",
            callback_data="smi_main"
        )
    )

    return builder.as_markup()


def cart_keyboard_smi(items_count: int, total_price: float) -> InlineKeyboardMarkup:
    """Корзина"""
    builder = InlineKeyboardBuilder()

    if items_count > 0:
        builder.row(
            InlineKeyboardButton(text="❌ Очистить", callback_data="smi_cart_clear"),
            InlineKeyboardButton(text="🛎️ Оформить", callback_data="smi_order_start")
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Главная", callback_data="smi_main"),
        InlineKeyboardButton(text="📦 Каталог", callback_data="smi_catalog")
    )

    return builder.as_markup()


def order_form_keyboard(step: str) -> InlineKeyboardMarkup:
    """Клавиатура для формы заказа"""
    builder = InlineKeyboardBuilder()

    if step == "pet_name":
        builder.row(
            InlineKeyboardButton(text="↩️ Отмена", callback_data="smi_cart")
        )
    elif step == "address":
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="smi_order_back_pet"),
            InlineKeyboardButton(text="↩️ Отмена", callback_data="smi_cart")
        )
    elif step == "telegram":
        builder.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="smi_order_back_address"),
            InlineKeyboardButton(text="↩️ Отмена", callback_data="smi_cart")
        )
    elif step == "confirm":
        builder.row(
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="smi_order_confirm"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="smi_order_edit")
        )
        builder.row(
            InlineKeyboardButton(text="↩️ Отмена", callback_data="smi_cart")
        )

    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Простая кнопка назад в меню"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Главная", callback_data="smi_main"))
    return builder.as_markup()