# app/handlers/admin/__init__.py - ОБНОВЛЕННЫЙ

from aiogram import Router
from .panel import router as panel_router
from .products import router as products_router
from .stock import router as stock_router
from .backup import router as backup_router  # НОВЫЙ ИМПОРТ

router = Router()
router.include_router(panel_router)
router.include_router(products_router)
router.include_router(stock_router)
router.include_router(backup_router)  # НОВЫЙ РОУТЕР