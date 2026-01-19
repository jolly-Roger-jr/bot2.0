# app/core/router.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
Централизованная система роутеров с плоской структурой.
"""
from aiogram import Router
import importlib


class RouterManager:
    """Менеджер для управления всеми роутерами с плоской структурой"""

    def __init__(self):
        self.main_router = Router()
        self._individual_routers = []

    def setup_routers(self):
        """Настройка всех роутеров - плоская структура без вложенности"""

        # 1. Создаем все роутеры заново (не импортируем из модулей)
        self._create_flat_routers()

        return self.main_router

    def _create_flat_routers(self):
        """Создаем плоскую структуру роутеров"""

        # Список всех модулей с хендлерами
        handler_modules = [
            # User handlers
            ('app.handlers.user.start', 'register_start_handlers'),
            ('app.handlers.user.catalog', 'register_catalog_handlers'),
            ('app.handlers.user.cart', 'register_cart_handlers'),
            ('app.handlers.user.order', 'register_order_handlers'),
            ('app.handlers.user.profile', 'register_profile_handlers'),
            ('app.handlers.user.qty', 'register_qty_handlers'),
            ('app.handlers.user.back', 'register_back_handlers'),

            # Admin handlers
            ('app.handlers.admin', 'register_admin_handlers'),
            ('app.handlers.admin.panel', 'register_panel_handlers'),
            ('app.handlers.admin.products', 'register_products_handlers'),
            ('app.handlers.admin.stock', 'register_stock_handlers'),
            ('app.handlers.admin.backup', 'register_backup_handlers'),
            ('app.handlers.admin.orders', 'register_orders_handlers'),
            ('app.handlers.admin.add_product', 'register_add_product_handlers'),
            ('app.handlers.admin.add_category', 'register_add_category_handlers'),
        ]

        # Создаем новый роутер для каждого модуля
        for module_name, register_func_name in handler_modules:
            try:
                # Импортируем модуль
                module = importlib.import_module(module_name)

                # Создаем новый роутер для этого модуля
                module_router = Router()

                # Регистрируем хендлеры в новом роутере
                if hasattr(module, register_func_name):
                    # Если есть функция регистрации
                    register_func = getattr(module, register_func_name)
                    register_func(module_router)
                else:
                    # Иначе регистрируем хендлеры из существующего роутера
                    if hasattr(module, 'router'):
                        existing_router = module.router
                        # Копируем хендлеры из существующего роутера
                        self._copy_handlers(existing_router, module_router)

                # Включаем роутер в главный
                self.main_router.include_router(module_router)
                self._individual_routers.append((module_name, module_router))

                print(f"✅ Создан роутер для: {module_name}")

            except Exception as e:
                print(f"❌ Ошибка при создании роутера для {module_name}: {e}")

    def _copy_handlers(self, source_router, target_router):
        """Копирует хендлеры из одного роутера в другой"""
        # Для сообщений
        for handler in source_router.message.handlers:
            target_router.message.register(handler.callback, *handler.filters)

        # Для callback
        for handler in source_router.callback_query.handlers:
            target_router.callback_query.register(handler.callback, *handler.filters)

    def get_stats(self):
        """Получить статистику по хендлерам"""
        stats = {
            'total_message_handlers': 0,
            'total_callback_handlers': 0,
            'modules': []
        }

        for module_name, router in self._individual_routers:
            try:
                msg_count = len(list(router.message.handlers))
                cb_count = len(list(router.callback_query.handlers))

                stats['total_message_handlers'] += msg_count
                stats['total_callback_handlers'] += cb_count

                stats['modules'].append({
                    'name': module_name,
                    'message_handlers': msg_count,
                    'callback_handlers': cb_count
                })
            except Exception as e:
                print(f"⚠️ Ошибка при получении статистики для {module_name}: {e}")
                continue

        return stats


# Глобальный экземпляр
router_manager = RouterManager()