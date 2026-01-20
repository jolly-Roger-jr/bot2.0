# app/handlers/__init__.py
"""
Главный файл регистрации всех хендлеров.
БЕЗ циклических импортов!
"""
import logging
from aiogram import Router

logger = logging.getLogger(__name__)

# Создаем главный роутер
main_router = Router()


def setup_handlers() -> Router:
    """
    Настройка всех хендлеров.
    Возвращает главный роутер.
    """
    logger.info("🔄 Регистрация хендлеров...")

    # 1. USER HANDLERS - регистрируем напрямую
    from .user import start, catalog, cart, order, profile, qty, back

    # Включаем все роутеры пользовательской части
    main_router.include_router(start.router)
    main_router.include_router(catalog.router)
    main_router.include_router(cart.router)
    main_router.include_router(order.router)
    main_router.include_router(profile.router)
    main_router.include_router(qty.router)
    main_router.include_router(back.router)

    logger.info("✅ User хендлеров: 7 роутеров")

    # 2. ADMIN HANDLERS - регистрируем напрямую
    from .admin import panel, products, stock, backup, orders, add_product, add_category

    main_router.include_router(panel.router)
    main_router.include_router(products.router)
    main_router.include_router(stock.router)
    main_router.include_router(backup.router)
    main_router.include_router(orders.router)
    main_router.include_router(add_product.router)
    main_router.include_router(add_category.router)

    logger.info("✅ Admin хендлеров: 7 роутеров")

    # 3. Общее количество
    total_routers = len([r for r in main_router.sub_routers])
    logger.info(f"🎯 Всего роутеров: {total_routers}")

    return main_router


def get_main_router() -> Router:
    """Получить главный роутер (создает при первом вызове)"""
    # Если роутеры еще не зарегистрированы, регистрируем
    if not main_router.sub_routers:
        return setup_handlers()
    return main_router