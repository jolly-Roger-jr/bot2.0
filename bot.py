"""
Точка входа в бота - простая и понятная
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher

from database import init_db
from handlers import router
from admin import admin_router
from backup import run_backup_scheduler
from config import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Глобальный объект бота для уведомлений
bot_instance = None


async def on_startup():
    """Действия при запуске бота"""
    global bot_instance
    logger.info("🚀 Запуск бота Barkery Shop...")
    
    # Инициализируем БД
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise
    
    # Запускаем планировщик резервного копирования с передачей бота
    await run_backup_scheduler(bot_instance)
    logger.info("✅ Планировщик резервного копирования запущен")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("⏹️ Остановка бота...")
    if bot_instance:
        await bot_instance.session.close()


async def main():
    """Главная функция запуска бота"""
    global bot_instance
    
    # Создаем бота и диспетчер
    bot_instance = Bot(token=settings.bot_token)
    dp = Dispatcher()
    
    # Подключаем роутеры
    dp.include_router(admin_router)
    dp.include_router(router)
    
    await on_startup()
    
    # Удаляем вебхук (если был)
    await bot_instance.delete_webhook(drop_pending_updates=True)
    
    logger.info(f"✅ Бот запущен. Админ ID: {settings.admin_id}")
    logger.info("✅ Ожидаем сообщений...")
    
    # Запускаем поллинг
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
