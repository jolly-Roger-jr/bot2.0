# app/bot.py - ОБНОВЛЕННЫЙ

import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router
from app.db.engine import engine
from app.db.models import Base
from app.scheduler import start_scheduler, setup_backup_schedule


async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    # Инициализация БД (создаем только если не существует)
    logger.info("Инициализация базы данных...")

    async with engine.begin() as conn:
        # Создаем таблицы только если они не существуют
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ База данных проверена/создана")

    # Настройка и запуск планировщика резервного копирования
    logger.info("Настройка планировщика резервного копирования...")
    setup_backup_schedule()
    start_scheduler()
    logger.info("✅ Планировщик запущен")

    # Инициализация бота
    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)

    logger.info("🚀 Бот запущен и готов к работе")
    logger.info(f"⏰ Резервное копирование настроено на 4:00 ({settings.timezone})")

    try:
        await dp.start_polling(bot)
    finally:
        # Очистка при завершении
        logger.info("Завершение работы бота...")
        from app.scheduler import stop_scheduler
        stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())