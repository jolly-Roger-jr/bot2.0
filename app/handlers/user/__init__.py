from aiogram import Router

from .start import router as start_router
from .catalog import router as catalog_router
from .cart import router as cart_router
from .order import router as order_router
from .qty import router as qty_router

router = Router()
router.include_router(start_router)
router.include_router(catalog_router)
router.include_router(cart_router)
router.include_router(order_router)
router.include_router(qty_router)