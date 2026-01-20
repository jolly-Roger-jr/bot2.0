# app/services/__init__.py

# Импортируем основные сервисы
from .catalog import get_categories, get_products_by_category, get_product
from .cart import (
    add_to_cart,
    get_cart_items,
    clear_cart,
    get_cart_total,
    update_cart_item,
    remove_from_cart,
    validate_cart_for_order,
    get_cart_summary
)

# Единый объект для импорта
services = None  # Инициализируем позже


def init_services():
    """Инициализация единого объекта services"""
    global services

    class Services:
        """Единый доступ ко всем сервисам"""

        # Каталог
        catalog = {
            'get_categories': get_categories,
            'get_products_by_category': get_products_by_category,
            'get_product': get_product
        }

        # Корзина
        cart = {
            'add_to_cart': add_to_cart,
            'get_cart_items': get_cart_items,
            'clear_cart': clear_cart,
            'get_cart_total': get_cart_total,
            'update_cart_item': update_cart_item,
            'remove_from_cart': remove_from_cart,
            'validate_cart_for_order': validate_cart_for_order,
            'get_cart_summary': get_cart_summary
        }

    services = Services()


# Инициализируем при импорте
init_services()

__all__ = [
    'services',
    'get_categories',
    'get_products_by_category',
    'get_product',
    'add_to_cart',
    'get_cart_items',
    'clear_cart',
    'get_cart_total',
    'update_cart_item',
    'remove_from_cart',
    'validate_cart_for_order',
    'get_cart_summary'
]