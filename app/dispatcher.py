from aiogram import Router, types
from app.handlers.user.start import router as start_router
from app.handlers.user.catalog import router as catalog_router
from app.handlers.user.cart import router as cart_router

debug_router = Router()

@debug_router.message()
async def catch_all(message: types.Message):
    print("🔥 MESSAGE RECEIVED:", message.text)

def setup_dispatcher(dp):
    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(debug_router)