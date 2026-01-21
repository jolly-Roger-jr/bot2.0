"""
Сервисы для Barkery_bot
Упрощенная версия без циклических импортов
"""

# Экспортируем только имена, реальные импорты будут ленивыми
__all__ = [
    'catalog',
    'cart',
    'orders',
    'stock',
    'notifications',
    'user_notifications',
    'pricing'
]


# Ленивые объекты сервисов
class LazyLoader:
    """Ленивая загрузка сервисов"""

    @property
    def catalog(self):
        from .catalog import get_categories, get_products_by_category, get_product
        return type('Catalog', (), {
            'get_categories': get_categories,
            'get_products_by_category': get_products_by_category,
            'get_product': get_product
        })()

    @property
    def cart(self):
        from .cart import (
            add_to_cart, get_cart_items, clear_cart, get_cart_total,
            update_cart_item, remove_from_cart, validate_cart_for_order,
            get_cart_summary
        )
        return type('Cart', (), {
            'add_to_cart': add_to_cart,
            'get_cart_items': get_cart_items,
            'clear_cart': clear_cart,
            'get_cart_total': get_cart_total,
            'update_cart_item': update_cart_item,
            'remove_from_cart': remove_from_cart,
            'validate_cart_for_order': validate_cart_for_order,
            'get_cart_summary': get_cart_summary
        })()

    @property
    def orders(self):
        from .orders import order_service
        return order_service

    @property
    def stock(self):
        from .stock import stock_service
        return stock_service

    @property
    def notifications(self):
        from .notifications import notify_admin_new_order, notify_admin
        return type('Notifications', (), {
            'notify_admin_new_order': notify_admin_new_order,
            'notify_admin': notify_admin
        })()

    @property
    def user_notifications(self):
        from .user_notifications import user_notification_service
        return user_notification_service

    @property
    def pricing(self):
        from .pricing import PricingService
        return PricingService()


# Создаем экземпляр для импорта
services = LazyLoader()


# Функции для обратной совместимости
def get_categories():
    from .catalog import get_categories as func
    return func


def get_products_by_category(category_name: str):
    from .catalog import get_products_by_category as func
    return func(category_name)


def get_product(product_id: int):
    from .catalog import get_product as func
    return func(product_id)