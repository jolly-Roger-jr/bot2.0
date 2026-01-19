# app/scheduler.py - Планировщик задач для Barkery_bot
import asyncio
import os
import shutil
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Создаем планировщик
scheduler = AsyncIOScheduler()


def setup_backup_schedule():
    """Настройка расписания резервного копирования"""
    try:
        # Ежедневное резервное копирование в 4:00 по сербскому времени
        scheduler.add_job(
            backup_database,
            CronTrigger(hour=4, minute=0, timezone=settings.timezone),
            id='daily_backup',
            name='Ежедневное резервное копирование БД',
            replace_existing=True
        )
        logger.info("✅ Расписание резервного копирования настроено (4:00 ежедневно)")
    except Exception as e:
        logger.error(f"❌ Ошибка настройки планировщика: {e}")


def start_scheduler():
    """Запуск планировщика"""
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ Планировщик задач запущен")


def stop_scheduler():
    """Остановка планировщика"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Планировщик задач остановлен")


async def backup_database():
    """Создание резервной копии базы данных в локальное и удаленное хранилище"""
    try:
        source_db = "barkery.db"
        if not os.path.exists(source_db):
            logger.warning("❌ Файл базы данных не найден")
            return False

        # 1. Локальное хранилище
        os.makedirs("backups", exist_ok=True)

        # Формируем имя файла с timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"barkery_backup_{timestamp}.db"
        local_backup_path = f"backups/{backup_filename}"

        # Копируем файл локально
        shutil.copy2(source_db, local_backup_path)
        logger.info(f"✅ Локальная резервная копия создана: {local_backup_path}")

        # 2. Удаленное хранилище (имитация - можно заменить на S3, FTP и т.д.)
        remote_success = await backup_to_remote_storage(local_backup_path, backup_filename)

        if remote_success:
            logger.info(f"✅ Резервная копия сохранена в удаленное хранилище: {backup_filename}")
        else:
            logger.warning("⚠️ Резервная копия не сохранена в удаленное хранилище")

        # 3. Очищаем старые бэкапы (оставляем последние 7)
        await cleanup_old_backups()

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при создании резервной копии: {e}")
        return False


async def backup_to_remote_storage(local_path: str, filename: str):
    """Сохранение резервной копии в удаленное хранилище"""
    try:
        # Имитация удаленного хранилища
        # В реальном проекте здесь будет код для S3, FTP, Google Drive и т.д.

        # Пример для S3 (ракомментировать при настройке):
        # import boto3
        # s3 = boto3.client('s3')
        # s3.upload_file(local_path, 'your-bucket-name', f'backups/{filename}')

        # Создаем директорию для имитации удаленного хранилища
        remote_dir = "remote_backups"
        os.makedirs(remote_dir, exist_ok=True)

        remote_path = f"{remote_dir}/{filename}"
        shutil.copy2(local_path, remote_path)

        # Логируем успех
        file_size = os.path.getsize(remote_path) / 1024  # KB
        logger.info(f"📁 Удаленная копия: {remote_path} ({file_size:.1f} KB)")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении в удаленное хранилище: {e}")
        return False


async def cleanup_old_backups():
    """Очистка старых резервных копий"""
    try:
        # Очистка локальных бэкапов
        if os.path.exists("backups"):
            backup_files = sorted(
                [f for f in os.listdir("backups") if f.endswith(".db")],
                key=lambda x: os.path.getctime(os.path.join("backups", x))
            )

            if len(backup_files) > 7:
                for old_file in backup_files[:-7]:
                    os