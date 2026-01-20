# app/scheduler.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.db.backup import backup_database
from app.utils.timezone import get_serbia_time

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone=settings.timezone)


def setup_backup_schedule():
    """Настройка ежедневного резервного копирования в 4:00"""
    try:
        scheduler.add_job(
            daily_backup_task,
            trigger=CronTrigger(hour=4, minute=0, timezone=settings.timezone),
            id='daily_backup',
            name='Ежедневное резервное копирование БД',
            replace_existing=True
        )
        logger.info("✅ Планировщик настроен на 4:00 каждый день")
    except Exception as e:
        logger.error(f"❌ Ошибка настройки планировщика: {e}")


async def daily_backup_task():
    """Задача ежедневного резервного копирования"""
    try:
        logger.info("🔄 Запуск ежедневного резервного копирования...")
        backup_path = await backup_database()
        logger.info(f"✅ Ежедневный бэкап создан: {backup_path}")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании бэкапа: {e}")


async def manual_backup_now():
    """Ручное создание резервной копии"""
    try:
        logger.info("🔄 Ручной запуск резервного копирования...")
        backup_path = await backup_database()
        serbia_time = get_serbia_time()
        logger.info(f"✅ Ручной бэкап создан: {backup_path}")
        return {
            'success': True,
            'path': backup_path,
            'timestamp': serbia_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при ручном бэкапе: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def start_scheduler():
    """Запуск планировщика"""
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ Планировщик задач запущен")
    else:
        logger.warning("⚠️ Планировщик уже запущен")