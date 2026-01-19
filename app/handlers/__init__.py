# app/handlers/__init__.py - КАНОНИЧНАЯ ВЕРСИЯ
from aiogram import Router


def setup_routers() -> Router:
    """
    Настройка всех роутеров.
    Это ЕДИНСТВЕННЫЙ правильный способ в aiogram 3.x
    """
    # Создаем главный роутер
    main_router = Router()

    # 1. User handlers
    from .user import router as user_router
    main_router.include_router(user_router)
    print("✅ User роутер зарегистрирован")

    # 2. Admin handlers
    from .admin import router as admin_router
    main_router.include_router(admin_router)
    print("✅ Admin роутер зарегистрирован")

    return main_router