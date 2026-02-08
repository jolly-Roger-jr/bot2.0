#!/usr/bin/env python3
"""
Barkery Shop
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database import init_db
from admin import admin_router
from handlers import router as main_router

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("🚀 Barkery Shop - Запуск бота")

    try:
        # Проверяем настройки
        settings.validate()
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        return

    # Инициализация
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Включаем роутеры
    dp.include_router(admin_router)
    dp.include_router(main_router)

    # Инициализация БД
    await init_db()

    logger.info(f"👑 Админ ID: {settings.admin_id}")
    logger.info("✅ Бот готов к работе")

    # Сбрасываем webhook
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏹️ Остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())