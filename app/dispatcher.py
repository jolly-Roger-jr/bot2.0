from aiogram import Dispatcher
from app.handlers.user import start, catalog, cart, order  # импортируем только роутеры, не dp

dp = Dispatcher()

# Регистрируем роутеры
# dp.include_router(start.router)
# dp.include_router(catalog.router)
# dp.include_router(cart.router)
# dp.include_router(order.router)

print("DISPATCHER LOADED")