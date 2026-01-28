"""
Бот с DEBUG логами
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db
from handlers import router
from admin import admin_router
from backup import run_backup_scheduler
from config import settings

# ВКЛЮЧАЕМ DEBUG ЛОГИ
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

async def on_startup():
    """Действия при запуске бота"""
    logger.info("🚀 Запуск бота Barkery Shop...")
    
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise
    
    await run_backup_scheduler()
    logger.info("✅ Планировщик резервного копирования запущен")

async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("⏹️ Остановка бота...")

async def main():
    """Главная функция запуска бота"""
    await on_startup()
    
    bot_instance = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # ПОДКЛЮЧАЕМ СНАЧАЛА АДМИНСКИЙ РОУТЕР!
    logger.debug("Подключаем админский роутер...")
    dp.include_router(admin_router)
    
    logger.debug("Подключаем основной роутер...")
    dp.include_router(router)
    
    await bot_instance.delete_webhook(drop_pending_updates=True)
    
    logger.info(f"✅ Бот запущен. Админ ID: {settings.admin_id}")
    logger.info("✅ Ожидаем сообщений...")
    
    try:
        await dp.start_polling(bot_instance)
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по запросу пользователя...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
