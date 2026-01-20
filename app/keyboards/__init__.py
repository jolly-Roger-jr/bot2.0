# app/keyboards/__init__.py
"""
Клавиатуры для Barkery_bot
Единый импорт всех клавиатур
"""

from .user import (
    categories_keyboard,
    products_keyboard,
    product_detail_keyboard,
    update_quantity_keyboard,
    cart_keyboard,
    cart_item_management_keyboard,
    confirm_keyboard,
    back_to_cart_keyboard,
    get_cart_button
)

from .admin import (
    admin_menu,
    stock_management_menu,
    back_to_admin_menu
)


# Единый объект для импорта
class Keyboards:
    """Единый доступ ко всем клавиатурам"""

    def __init__(self):
        # Пользовательские
        self.user = {
            'categories': categories_keyboard,
            'products': products_keyboard,
            'product_detail': product_detail_keyboard,
            'update_quantity': update_quantity_keyboard,
            'cart': cart_keyboard,
            'cart_item_management': cart_item_management_keyboard,
            'confirm': confirm_keyboard,
            'back_to_cart': back_to_cart_keyboard,
            'get_cart_button': get_cart_button
        }

        # Админские
        self.admin = {
            'menu': admin_menu,
            'stock_management': stock_management_menu,
            'back_to_admin': back_to_admin_menu
        }


# Создаем экземпляр при импорте
keyboards = Keyboards()

__all__ = [
    'keyboards',
    'categories_keyboard',
    'products_keyboard',
    'product_detail_keyboard',
    'update_quantity_keyboard',
    'cart_keyboard',
    'cart_item_management_keyboard',
    'confirm_keyboard',
    'back_to_cart_keyboard',
    'get_cart_button',
    'admin_menu',
    'stock_management_menu',
    'back_to_admin_menu'
]