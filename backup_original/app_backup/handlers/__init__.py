# app/handlers/__init__.py
from aiogram import Router

# Создаем главный роутер
main_router = Router()


def setup_routers():
    """Настройка роутеров с ленивыми импортами"""
    # User роутеры
    from .user import router as user_router
    main_router.include_router(user_router)

    # Admin роутеры
    from .admin import router as admin_router
    main_router.include_router(admin_router)

    return main_router


# Инициализируем роутеры
setup_routers()

__all__ = ['main_router']