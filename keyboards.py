"""
Все клавиатуры для Barkery Shop (только Inline)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== ПОЛЬЗОВАТЕЛЬСКИЕ КЛАВИАТУРЫ ==========

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📦 Каталог", callback_data="catalog")
    )

    builder.row(
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart"),
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
    )

    builder.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    )

    return builder.as_markup()

def categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Клавиатура с категориями"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {category['name']}",
                callback_data=f"category:{category['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Главная", callback_data="main_menu"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_check")  # Было cart
    )

    return builder.as_markup()


def products_keyboard(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с товарами категории - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    builder = InlineKeyboardBuilder()

    for product in products:
        # ИСПРАВЛЕНО: Определяем отображение цены в зависимости от типа товара
        unit_type = product.get('unit_type', 'grams')
        if unit_type == 'grams':
            price_text = f"{product['price']} RSD/100г"
        else:  # pieces
            price_text = f"{product['price']} RSD/шт"

        stock_status = "✅" if product['available'] and product['stock_grams'] > 0 else "⏳"

        builder.row(
            InlineKeyboardButton(
                text=f"{stock_status} {product['name']} - {price_text}",
                callback_data=f"product:{product['id']}:{category_id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_check")
    )

    return builder.as_markup()

def product_card_keyboard(product_id: int, category_id: int, current_qty: int = 0, unit_type: str = 'grams', measurement_step: int = 100) -> InlineKeyboardMarkup:
    """Карточка товара с кнопками +/-"""
    builder = InlineKeyboardBuilder()

    # Количество в единицах измерения
    if unit_type == 'grams':
        # Для грамм показываем точное количество, а не количество шагов
        qty_units = current_qty
        unit_text = f'{measurement_step}г'
        unit_symbol = 'г'
    else:  # pieces
        qty_units = current_qty
        unit_text = 'шт'
        unit_symbol = 'шт'


    # Ряд 1: кнопки +/-
    builder.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"qty_dec:{product_id}:{category_id}"
        ),
        InlineKeyboardButton(
            text=f"{qty_units} {unit_symbol}",
            callback_data=f"qty_info:{product_id}"
        ),
        InlineKeyboardButton(
            text="➕",
            callback_data=f"qty_inc:{product_id}:{category_id}"
        )
    )

    # Ряд 2: Добавить в корзину
    add_qty = qty_units
    if add_qty > 0:
        builder.row(
            InlineKeyboardButton(
                text=f'🛒 Добавить ({add_qty}{unit_symbol})',
                callback_data=f"cart_add:{product_id}:{add_qty}:{category_id}"
            )
        )

    # Ряд 3: Навигация
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"category:{category_id}"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart_check")  # Добавить, если нет
    )

    return builder.as_markup()

def cart_keyboard(cart_items: list, total_price: float) -> InlineKeyboardMarkup:
    """Клавиатура корзины"""
    builder = InlineKeyboardBuilder()

    # Кнопки управления корзиной
    builder.row(
        InlineKeyboardButton(text="❌ Очистить все", callback_data="cart_clear"),
        InlineKeyboardButton(text="🛎️ Оформить", callback_data="order_create")
    )

    # Навигация
    builder.row(
        InlineKeyboardButton(text="⬅️ Главная", callback_data="main_menu"),
        InlineKeyboardButton(text="📦 Каталог", callback_data="catalog")
    )

    return builder.as_markup()

def order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение заказа"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="order_confirm"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="cart_check")
    )

    builder.row(
        InlineKeyboardButton(text="⬅️ Главная", callback_data="main_menu")
    )

    return builder.as_markup()

def help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="⬅️ Главная", callback_data="main_menu")
    )

    return builder.as_markup()

# ========== АДМИНСКИЕ КЛАВИАТУРЫ ==========

def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админки"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📦 Управление категориями", callback_data="admin_categories"),
        InlineKeyboardButton(text="🛒 Управление товарами", callback_data="admin_products")
    )

    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_statistics")
    )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")
    )

    return builder.as_markup()

def admin_categories_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Клавиатура управления категориями"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {category['name']}",
                callback_data=f"admin_category_products:{category['id']}"
            ),
            InlineKeyboardButton(
                text="✏️",
                callback_data=f"admin_edit_category:{category['id']}"
            ),
            InlineKeyboardButton(
                text="❌",
                callback_data=f"admin_delete_category:{category['id']}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_add_category"),
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
    )

    return builder.as_markup()

def admin_products_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории"""
    builder = InlineKeyboardBuilder()

    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {category.name}",
                callback_data=f"admin_category_products:{category.id}"
            )
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_back"),
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")
    )

    return builder.as_markup()


def admin_product_management_keyboard(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления товарами с гипоаллергенностью"""
    builder = InlineKeyboardBuilder()

    for product in products:
        status = "✅" if product["available"] else "⛔"

        # Иконка гипоаллергенности
        hypo_icon = "🎃🐟" if product.get('is_hypoallergenic', False) else "⚪"

        # Определяем отображение остатков
        unit_type = product.get('unit_type', 'grams')
        if unit_type == 'grams':
            stock_status = f"{product['stock_grams']}г"
        else:  # pieces
            stock_status = f"{product['stock_grams']}шт"

        # РЯД 1: Название товара с иконками
        builder.row(
            InlineKeyboardButton(
                text=f"{status}{hypo_icon} {product['name']} - {product['price']}RSD ({stock_status})",
                callback_data=f"admin_edit_product_full:{product['id']}:{category_id}"
            )
        )

        # РЯД 2: Быстрые действия
        builder.row(
            InlineKeyboardButton(
                text="🔄 Вкл/Выкл",
                callback_data=f"admin_toggle_product:{product['id']}:{category_id}"
            ),
            InlineKeyboardButton(
                text="💰 Цена",
                callback_data=f"admin_edit_product_price:{product['id']}:{category_id}"
            ),
            InlineKeyboardButton(
                text="📦 Остатки",
                callback_data=f"admin_update_stock:{product['id']}:{category_id}"
            )
        )

        # РЯД 3: Дополнительные действия
        builder.row(
            InlineKeyboardButton(
                text="🔬 Гипо",
                callback_data=f"admin_toggle_hypoallergenic:{product['id']}:{category_id}"
            ),
            InlineKeyboardButton(
                text="✏️ Название",
                callback_data=f"admin_edit_product_name:{product['id']}:{category_id}"
            ),
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"admin_delete_product:{product['id']}:{category_id}"
            )
        )

    # РЯД 4: Навигация
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="admin_products"),
        InlineKeyboardButton(text="🏠 В главное", callback_data="admin_back")
    )

    return builder.as_markup()


def admin_product_edit_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура редактирования товара"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="✏️ Изменить название",
            callback_data=f"admin_edit_product_name:{product_id}:{category_id}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="💰 Изменить цену",
            callback_data=f"admin_edit_product_price:{product_id}:{category_id}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📦 Изменить остатки",
            callback_data=f"admin_edit_product_stock:{product_id}:{category_id}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="📝 Изменить описание",
            callback_data=f"admin_edit_product_description:{product_id}:{category_id}"
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"admin_category_products:{category_id}"
        ),
        InlineKeyboardButton(
            text="🏠 В главное",
            callback_data="admin_back"
        )
    )

    return builder.as_markup()

# Обновленная функция главного меню админки (или замените существующую)
def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админки"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📦 Управление категориями", callback_data="admin_categories"),
        InlineKeyboardButton(text="🛒 Управление товарами", callback_data="admin_products")
    )

    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_statistics")
    )

    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")
    )

    return builder.as_markup()


# ========== НОВАЯ КЛАВИАТУРА ДЛЯ ВЫБОРА АДРЕСА ==========

def address_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора адреса: Да / Нет"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="address_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="address_no")
    )
    
    return builder.as_markup()
