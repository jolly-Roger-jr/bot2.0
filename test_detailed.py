# test_structure.py

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import settings
from app.handlers import main_router


async def test():
    print("🔍 Тестирование структуры роутеров...")

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)

    # Проверяем хендлеры
    message_handlers = list(dp.message.handlers)
    callback_handlers = list(dp.callback_query.handlers)

    print(f"📊 Всего хендлеров: {len(message_handlers)} сообщений, {len(callback_handlers)} callback")

    # Проверяем подроутеры
    print(f"\n📁 Подроутеры в main_router: {len(main_router.sub_routers)}")

    for i, router in enumerate(main_router.sub_routers, 1):
        msg = list(router.message.handlers)
        cb = list(router.callback_query.handlers)
        print(f"  {i}. Хендлеры: {len(msg)} сообщений, {len(cb)} callback")

    print("\n✅ Тест завершен")


if __name__ == "__main__":
    asyncio.run(test())