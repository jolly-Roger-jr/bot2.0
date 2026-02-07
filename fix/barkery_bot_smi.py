# barkery_bot_smi.py
"""
Barkery Shop - Single Message Interface версия
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import settings
from database import init_db
from admin import admin_router
from handlers_smi import router_smi as smi_router

# Настраиваем логирование
from logging_config import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 Barkery Shop - SINGLE MESSAGE INTERFACE")
    logger.info("=" * 50)
    logger.info("📱 Один message на весь сеанс")
    logger.info("🧹 Без артефактов в переписке")
    logger.info("⚡ Быстрая навигация")
    logger.info("=" * 50)

    # Инициализация
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Включаем роутеры
    dp.include_router(admin_router)  # Админка работает как обычно
    dp.include_router(smi_router)    # SMI для пользователей

    # Инициализация БД
    await init_db()

    # Сбрасываем webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Webhook сброшен")

    # Запуск
    try:
        logger.info("⏳ Запускаю polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏹️ Остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    asyncio.run(main())