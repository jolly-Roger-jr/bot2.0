import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.config import BOT_TOKEN
from app.dispatcher import setup_dispatcher

async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    setup_dispatcher(dp)

    logging.info("✅ Dispatcher and routers are set up, starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())