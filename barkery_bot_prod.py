"""
Barkery Shop - Продакшен версия
"""
import asyncio
import logging
import sys
from pathlib import Path

# Добавляем путь для импорта
sys.path.append(str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Используем продакшен конфигурацию
from config_prod import settings
from database import init_db
from admin import admin_router
from handlers import router as main_router
from health_check import health_monitor
from monitoring import monitor_performance

# Настраиваем логирование
from logging_config import setup_logging


# Усиленное логирование для продакшена
def setup_production_logging():
    """Настройка логирования для продакшена"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Основной лог
    main_log = log_dir / "barkery_prod.log"

    # Лог ошибок
    error_log = log_dir / "errors.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    root_logger.handlers.clear()

    # Файловый обработчик для основного лога
    file_handler = logging.FileHandler(
        main_log,
        encoding='utf-8',
        mode='a'
    )
    file_handler.setLevel(logging.INFO)

    # Файловый обработчик для ошибок
    error_handler = logging.FileHandler(
        error_log,
        encoding='utf-8',
        mode='a'
    )
    error_handler.setLevel(logging.ERROR)

    # Консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"Production logging initialized. Environment: {settings.ENVIRONMENT}")


async def main():
    """Главная функция запуска бота"""
    logger = logging.getLogger(__name__)

    try:
        # Настройка логирования
        setup_production_logging()

        logger.info("=" * 50)
        logger.info("🚀 Barkery Shop - PRODUCTION")
        logger.info(f"📅 {settings.ENVIRONMENT.upper()} ENVIRONMENT")
        logger.info("=" * 50)

        # Проверка конфигурации
        config_info = settings.get_info()
        logger.info(f"📋 Конфигурация: {config_info}")

        # Инициализация бота
        bot = Bot(
            token=settings.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher()

        # Устанавливаем пустые команды
        await bot.set_my_commands([])

        # Включаем роутеры
        dp.include_router(admin_router)
        dp.include_router(main_router)

        # Инициализация БД
        logger.info("💾 Инициализация базы данных...")
        await init_db()

        # Настройка системы бекапов
        logger.info("💾 Настройка системы бекапов...")
        from backup_enhanced import setup_backup_system
        backup_ready = await setup_backup_system()

        if backup_ready:
            logger.info("✅ Система бекапов настроена")
        else:
            logger.warning("⚠️ Проблемы с настройкой системы бекапов")

        # Сбрасываем webhook
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook сброшен")

        # Запуск мониторинга
        health_status = await health_monitor.check_health()
        logger.info(f"📊 Состояние системы: {health_status['status']}")

        # Информация о запуске
        logger.info(f"👑 Админ: {settings.ADMIN_ID}")
        logger.info(f"📁 База данных: {settings.DATABASE_URL}")
        logger.info(f"🔄 Бекапы: {settings.BACKUP_DIR}")
        logger.info("✅ Бот готов к работе!")
        logger.info("=" * 50)

        # Запуск polling
        logger.info("⏳ Запускаю polling...")
        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.info("⏹️ Остановлен пользователем")

        # Логирование остановки
        from logging_config import OperationLogger
        OperationLogger.log_operation(
            operation="bot_shutdown",
            status="info",
            details={"reason": "keyboard_interrupt"}
        )

    except Exception as e:
        logger.error(f"❌ Критическая ошибка запуска: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Логирование ошибки
        from logging_config import OperationLogger
        OperationLogger.log_operation(
            operation="bot_startup",
            status="error",
            error=str(e)
        )

        # Уведомление админу
        try:
            from error_handling_enhanced import error_handler
            await error_handler.handle_error(e, "bot_startup")
        except:
            pass

        raise


if __name__ == "__main__":
    asyncio.run(main())