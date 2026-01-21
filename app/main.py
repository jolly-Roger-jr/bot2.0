# app/main.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message  # ← ВАЖНО: добавить этот импорт!

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def setup_bot():
    """Настройка бота"""
    from app.config import settings

    token = settings.bot_token
    if not token or token == "":
        logger.error("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
        return None, None

    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    return bot, dp


async def register_handlers(dp):
    """Регистрация всех хендлеров"""
    # USER HANDLERS
    from app.handlers.user.start import router as start_router
    from app.handlers.user.catalog import router as catalog_router
    from app.handlers.user.cart import router as cart_router
    from app.handlers.user.order import router as order_router
    from app.handlers.user.profile import router as profile_router
    from app.handlers.user.qty import router as qty_router
    from app.handlers.user.back import router as back_router

    dp.include_router(start_router)
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(order_router)
    dp.include_router(profile_router)
    dp.include_router(qty_router)
    dp.include_router(back_router)

    logger.info("✅ User хендлеров подключено: 7 роутеров")

    # ADMIN HANDLERS с middleware
    from app.handlers.admin.panel import router as admin_panel_router
    from app.handlers.admin.products import router as admin_products_router
    from app.handlers.admin.stock import router as admin_stock_router
    from app.handlers.admin.backup import router as admin_backup_router
    from app.handlers.admin.orders import router as admin_orders_router
    from app.handlers.admin.add_product import router as admin_add_product_router
    from app.handlers.admin.add_category import router as admin_add_category_router

    from app.middlewares.admin_check import get_admin_middleware

    # Получаем middleware
    admin_middleware = get_admin_middleware()

    # Применяем к каждому админскому роутеру
    admin_routers = [
        admin_panel_router,
        admin_products_router,
        admin_stock_router,
        admin_backup_router,
        admin_orders_router,
        admin_add_product_router,
        admin_add_category_router,
    ]

    for router in admin_routers:
        router.message.middleware(admin_middleware)
        router.callback_query.middleware(admin_middleware)

    # Включаем роутеры
    for router in admin_routers:
        dp.include_router(router)

    logger.info("✅ Admin хендлеров подключено: 7 роутеров (с middleware)")

    return dp


async def setup_database():
    """Настройка базы данных"""
    try:
        from app.db.engine import engine, Base
        from app.db.init_db import init_database

        # Создаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблицы базы данных созданы")

        # Инициализируем тестовые данные
        await init_database()
        logger.info("✅ Тестовые данные добавлены")

    except Exception as e:
        logger.warning(f"⚠️ База данных: {e}")


async def setup_scheduler():
    """Настройка планировщика"""
    try:
        from app.scheduler import setup_backup_schedule, start_scheduler
        setup_backup_schedule()
        start_scheduler()
        logger.info("✅ Планировщик резервного копирования запущен")
    except Exception as e:
        logger.warning(f"⚠️ Планировщик: {e}")


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск Barkery Bot...")

    # 1. Настраиваем бота
    bot, dp = await setup_bot()
    if not bot or not dp:
        return

    # 2. Регистрируем хендлеры
    dp = await register_handlers(dp)

    # 3. Добавляем тестовый обработчик для ВСЕХ сообщений
    @dp.message()
    async def handle_all_messages(message: Message):
        """Обработчик всех сообщений для теста"""
        logger.info(f"📨 Получено сообщение: {message.text} от {message.from_user.id}")

        if message.text:
            if message.text.startswith('/'):
                await message.answer(f"Команда получена: {message.text}")
            else:
                await message.answer(f"Вы написали: {message.text}")

    # 4. Настраиваем БД
    await setup_database()

    # 5. Настраиваем планировщик
    await setup_scheduler()

    # 6. Запускаем бота
    logger.info("\n" + "=" * 50)
    logger.info("🚀 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    logger.info("📱 Основные команды: /start, /cart, /help, /admin")
    logger.info("=" * 50)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("🔄 Начинаю polling...")
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("\n⏹ Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске polling: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await bot.session.close()
        logger.info("👋 Бот завершил работу")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Завершение работы")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)