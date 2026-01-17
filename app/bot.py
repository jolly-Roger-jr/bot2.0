import asyncio
import logging
from aiogram import Bot, Dispatcher
from app.config import BOT_TOKEN
from app.handlers.user import router as user_router
from app.db.engine import engine
from app.db.base import Base

TOKEN = "PUT_YOUR_TOKEN_HERE"

async def main():
    logging.basicConfig(level=logging.INFO)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())