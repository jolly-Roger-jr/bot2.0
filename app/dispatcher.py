from aiogram import Dispatcher
from app.handlers.user import start, catalog, cart  # импортируем только роутеры, не dp

dp = Dispatcher()

# Регистрируем роутеры
dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(cart.router)

print("DISPATCHER LOADED")