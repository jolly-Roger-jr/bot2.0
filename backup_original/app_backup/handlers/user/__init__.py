# app/handlers/user/__init__.py
from aiogram import Router

# Создаем единый роутер для пользователей
router = Router()


def setup_user_routers():
    """Настройка user роутеров с ленивыми импортами"""
    # Импортируем все user роутеры
    from .start import router as start_router
    from .catalog import router as catalog_router
    from .cart import router as cart_router
    from .order import router as order_router
    from .profile import router as profile_router
    from .qty import router as qty_router
    from .back import router as back_router

    # Включаем все подроутеры
    router.include_router(start_router)
    router.include_router(catalog_router)
    router.include_router(cart_router)
    router.include_router(order_router)
    router.include_router(profile_router)
    router.include_router(qty_router)
    router.include_router(back_router)


# Вызываем настройку
setup_user_routers()

__all__ = ['router']