# app/main.py
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск Barkery Bot...")

    # 1. Загружаем настройки
    try:
        from app.config import settings

        token = settings.bot_token
        if not token or token == "":
            logger.error("❌ ОШИБКА: BOT_TOKEN не найден в .env файле!")
            logger.info("Добавьте в .env: BOT_TOKEN=ваш_токен_бота")
            return

        logger.info(f"✅ Настройки загружены. Admin ID: {settings.admin_id}")

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки настроек: {e}")
        return

    # 2. Создаем бота и диспетчер
    try:
        bot = Bot(token=token)
        dp = Dispatcher(storage=MemoryStorage())
        logger.info("✅ Бот и диспетчер созданы")

    except Exception as e:
        logger.error(f"❌ Ошибка создания бота: {e}")
        return

    # 3. Регистрируем все хендлеры
    try:
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

        # ADMIN HANDLERS
        from app.handlers.admin.panel import router as admin_panel_router
        from app.handlers.admin.products import router as admin_products_router
        from app.handlers.admin.stock import router as admin_stock_router
        from app.handlers.admin.backup import router as admin_backup_router
        from app.handlers.admin.orders import router as admin_orders_router
        from app.handlers.admin.add_product import router as admin_add_product_router
        from app.handlers.admin.add_category import router as admin_add_category_router

        dp.include_router(admin_panel_router)
        dp.include_router(admin_products_router)
        dp.include_router(admin_stock_router)
        dp.include_router(admin_backup_router)
        dp.include_router(admin_orders_router)
        dp.include_router(admin_add_product_router)
        dp.include_router(admin_add_category_router)

        logger.info("✅ Admin хендлеров подключено: 7 роутеров")

        # Команда /admin
        @dp.message(lambda message: message.text == "/admin")
        async def admin_command(message):
            from app.config import settings
            from app.keyboards.admin import admin_menu

            if str(message.from_user.id) != str(settings.admin_id):
                await message.answer("❌ У вас нет доступа к этой команде")
                return

            await message.answer(
                "⚙️ <b>Админ-панель Barkery</b>\n\n"
                "Выберите раздел для управления:",
                parse_mode="HTML",
                reply_markup=admin_menu()
            )
            logger.info(f"Admin команда вызвана пользователем {message.from_user.id}")

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта хендлеров: {e}")
        import traceback
        traceback.print_exc()
        return
    except Exception as e:
        logger.error(f"❌ Ошибка регистрации хендлеров: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Инициализируем БД
    try:
        from app.db.engine import engine
        from app.db.models import Base
        from app.db.init_db import init_database

        # Создаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Таблицы базы данных созданы")

        # Инициализируем тестовые данные (опционально, можно убрать)
        # await init_database()
        # logger.info("✅ Тестовые данные добавлены")

    except Exception as e:
        logger.warning(f"⚠️ База данных: {e}")

    # 5. Запускаем планировщик
    try:
        from app.scheduler import setup_backup_schedule, start_scheduler
        setup_backup_schedule()
        start_scheduler()
        logger.info("✅ Планировщик резервного копирования запущен")
    except Exception as e:
        logger.warning(f"⚠️ Планировщик: {e}")

    # 6. ЗАПУСКАЕМ БОТА
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