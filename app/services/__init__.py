# app/services/__init__.py
from .catalog import get_categories, get_products_by_category, get_product
from .cart import (
    add_to_cart,
    get_cart_items,
    clear_cart,
    get_cart_total,
    update_cart_item,
    remove_from_cart,
    validate_cart_for_order
)
from .stock import stock_service
from .orders import order_service
from .notifications import notify_admin, notify_admin_new_order
from .user_notifications import user_notification_service

__all__ = [
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
    'stock_service',
    'order_service',
    'notify_admin',
    'notify_admin_new_order',
    'user_notification_service'
]