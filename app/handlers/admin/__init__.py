# app/handlers/admin/__init__.py - ИСПРАВЛЕННЫЙ
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from app.config import settings

# Создаем основной роутер для админки
router = Router()


@router.message(Command("admin"))
async def admin_command(message: Message):
    """Обработчик команды /admin"""
    if str(message.from_user.id) != str(settings.admin_id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    from app.keyboards.admin import admin_menu
    await message.answer("⚙️ Админ-панель Barkery", reply_markup=admin_menu())


# Включаем все подроутеры напрямую (без циклических импортов)
from . import panel
from . import products
from . import stock
from . import backup
from . import orders
from . import add_product
from . import add_category

router.include_router(panel.router)
router.include_router(products.router)
router.include_router(stock.router)
router.include_router(backup.router)
router.include_router(orders.router)
router.include_router(add_product.router)
router.include_router(add_category.router)

__all__ = ['router']