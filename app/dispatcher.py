# app/dispatcher.py
from aiogram import Dispatcher
from app.handlers.user import start, catalog, cart

dp = Dispatcher()

# Регистрируем все роутеры
dp.include_router(start.router)
dp.include_router(catalog.router)
dp.include_router(cart.router)

print("DISPATCHER LOADED")