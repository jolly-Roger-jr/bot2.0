#!/usr/bin/env python3
"""
Barkery Shop - Чистая версия
Интернет-магазин натуральных собачьих лакомств
"""
from logging_config import setup_logging, OperationLogger  # Добавьте эту строку
import asyncio
import logging
setup_logging()
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database import init_db
from admin import admin_router  # Импортируем ПЕРВЫМ
from handlers import router as main_router

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Barkery Shop - ЧИСТАЯ ВЕРСИЯ")
    logger.info("=" * 50)

    # Инициализация
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Устанавливаем настройки бота для удаления клавиатур
    await bot.set_my_commands([])

    # ВАЖНО: Админский роутер должен быть ПЕРВЫМ,
    # чтобы он перехватывал админские колбэки
    dp.include_router(admin_router)
    dp.include_router(main_router)

    # Инициализация БД
    await init_db()

    logger.info(f"👑 Админ ID: {settings.admin_id}")
    logger.info("📱 Только Inline клавиатуры")
    logger.info("🛒 Полный функционал корзины")
    logger.info("✅ Упрощенная архитектура")
    logger.info("=" * 50)

    # Сбрасываем webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook сброшен")

    # Запуск
    try:
        logger.info("⏳ Запускаю polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏹️ Остановлен пользователем")
        OperationLogger.log_operation(
            operation="bot_shutdown",
            status="info",
            details={"reason": "keyboard_interrupt"}
        )
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        OperationLogger.log_operation(
            operation="bot_shutdown",
            status="error",
            error=str(e)
        )
        raise

if __name__ == "__main__":
    asyncio.run(main())
