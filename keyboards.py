"""
Все клавиатуры для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


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
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    )
    
    return builder.as_markup()


def products_keyboard(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура с товарами категории"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        price_text = f"{product['price']} RSD/100г"
        stock_status = "✅" if product['available'] and product['stock_grams'] > 0 else "⏳"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{stock_status} {product['name']} - {price_text}",
                callback_data=f"product:{product['id']}:{category_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_categories"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    )
    
    return builder.as_markup()


def product_card_keyboard(product_id: int, category_id: int, current_qty: int = 0) -> InlineKeyboardMarkup:
    """
    Карточка товара с кнопками +/- - УПРОЩЕННАЯ ВЕРСИЯ
    """
    builder = InlineKeyboardBuilder()
    
    # Количество в единицах по 100г
    qty_100g = current_qty // 100
    
    # Ряд 1: кнопки +/- (ПРОСТОЙ формат callback_data)
    builder.row(
        InlineKeyboardButton(
            text="➖",
            callback_data=f"qty_dec:{product_id}:{category_id}"
        ),
        InlineKeyboardButton(
            text=f"{qty_100g} × 100г",
            callback_data=f"qty_info:{product_id}:{current_qty}"
        ),
        InlineKeyboardButton(
            text="➕",
            callback_data=f"qty_inc:{product_id}:{category_id}"
        )
    )
    
    # Ряд 2: Добавить в корзину
    add_qty = qty_100g * 100
    if add_qty > 0:
        builder.row(
            InlineKeyboardButton(
                text=f"🛒 Добавить ({add_qty}г)",
                callback_data=f"cart_add:{product_id}:{add_qty}:{category_id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🛒 Добавить в корзину",
                callback_data=f"show_hint:select_quantity_first"
            )
        )
    
    # Ряд 3: Навигация
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_products:{category_id}"),
        InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")
    )
    
    return builder.as_markup()


def cart_keyboard(cart_items: list, total_price: float) -> InlineKeyboardMarkup:
    """Упрощенная клавиатура корзины - только кнопки управления"""
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
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="cart_refresh")
    )
    
    return builder.as_markup()

def order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение заказа"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="order_confirm"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="order_edit")
    )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Корзина", callback_data="cart"),
        InlineKeyboardButton(text="📦 Каталог", callback_data="catalog")
    )
    
    return builder.as_markup()


def back_to_category_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Кнопка возврата к категории"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад к товарам",
            callback_data=f"back_to_products:{category_id}"
        )
    )
    
    return builder.as_markup()

def admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админки"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📦 Управление категориями", callback_data="admin_categories"),
        InlineKeyboardButton(text="🛒 Управление товарами", callback_data="admin_products")
    )
    
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
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
    """Клавиатура выбора категории для управления товарами"""
    builder = InlineKeyboardBuilder()
    
    for category in categories:
        builder.row(
            InlineKeyboardButton(
                text=f"📦 {category.name}",
                callback_data=f"admin_category_products:{category.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
    )
    
    return builder.as_markup()


def admin_product_management_keyboard(products: list, category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления конкретными товарами"""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        status = "✅" if product["available"] else "⛔"
        stock_status = f"{product['stock_grams']}г"
        
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {product['name']} - {product['price']}RSD ({stock_status})",
                callback_data="no_action"
            )
        )
        
        builder.row(
            InlineKeyboardButton(
                text="🔄 Вкл/Выкл",
                callback_data=f"admin_toggle_product:{product['id']}:{category_id}"
            ),
            InlineKeyboardButton(
                text="📦 Остатки",
                callback_data=f"admin_update_stock:{product['id']}:{category_id}"
            ),
            InlineKeyboardButton(
                text="❌ Удалить",
                callback_data=f"admin_delete_product:{product['id']}:{category_id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data="admin_products"),
        InlineKeyboardButton(text="🏠 В главное", callback_data="admin_back")
    )
    
    return builder.as_markup()
