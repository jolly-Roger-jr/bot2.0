# app/scheduler.py

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.utils.timezone import SERBIA_TZ
from app.db.backup import backup_database

# Глобальный планировщик
scheduler = AsyncIOScheduler(timezone=str(SERBIA_TZ))


def setup_backup_schedule():
    """Настройка ежедневного резервного копирования в 4:00"""

    # Отключаем планировщик если он уже запущен
    if scheduler.running:
        scheduler.shutdown()

    # Настраиваем задание на 4:00 каждый день
    scheduler.add_job(
        backup_database,
        trigger=CronTrigger(
            hour=4,
            minute=0,
            timezone=SERBIA_TZ
        ),
        id='daily_backup',
        name='Ежедневное резервное копирование БД',
        replace_existing=True,
        max_instances=1
    )

    # Дополнительное задание: логирование о работе планировщика каждый час
    scheduler.add_job(
        log_scheduler_status,
        trigger=CronTrigger(
            minute=0,  # каждый час в 0 минут
            timezone=SERBIA_TZ
        ),
        id='hourly_log',
        name='Часовой лог статуса планировщика'
    )

    print(f"✅ Планировщик настроен на резервное копирование каждый день в 4:00 ({settings.timezone})")


async def log_scheduler_status():
    """Логирование статуса планировщика"""
    jobs = scheduler.get_jobs()
    print(f"📋 Статус планировщика: {len(jobs)} заданий")
    for job in jobs:
        next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'
        print(f"  • {job.name}: следующее выполнение в {next_run}")


async def manual_backup_now():
    """Ручное создание резервной копии (для админки)"""
    print("🔄 Запуск ручного резервного копирования...")
    result = await backup_database()
    return result


async def check_low_stock(bot: Bot):
    """Проверка низких остатков и уведомление админа"""
    from app.services.stock import stock_service
    low_stock = await stock_service.get_low_stock_products(threshold=500)

    if low_stock:
        message = "⚠️ <b>Низкие остатки:</b>\n\n"
        for product in low_stock:
            message += f"• {product.name}: {product.stock_grams}г\n"

        await bot.send_message(
            chat_id=settings.admin_id,
            text=message,
            parse_mode='HTML'
        )


def start_scheduler():
    """Запуск планировщика"""
    if not scheduler.running:
        scheduler.start()
        print("🚀 Планировщик резервного копирования запущен")

        # Выводим информацию о запланированных заданиях
        asyncio.create_task(log_scheduler_status())
    else:
        print("⚠️ Планировщик уже запущен")


def stop_scheduler():
    """Остановка планировщика"""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("🛑 Планировщик остановлен")