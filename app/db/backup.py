# app/db/backup.py - ПОЛНОСТЬЮ ИСПРАВЛЕННЫЙ
import asyncio
import aiofiles
import os
from datetime import datetime
from pathlib import Path
from app.config import settings


class DatabaseBackup:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        self.source_db = Path(db_path)

    async def create_backup(self) -> str:
        """Создать резервную копию базы данных"""
        if not self.source_db.exists():
            raise FileNotFoundError(f"Основная БД не найдена: {self.source_db}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"barkery_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        try:
            async with aiofiles.open(self.source_db, 'rb') as src:
                async with aiofiles.open(backup_path, 'wb') as dst:
                    content = await src.read()
                    await dst.write(content)

            file_size = os.path.getsize(backup_path) / 1024
            print(f"✅ Резервная копия создана: {backup_path} ({file_size:.2f} KB)")

            await self._cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            print(f"❌ Ошибка при создании резервной копии: {e}")
            raise

    async def _cleanup_old_backups(self, keep_days: int = 7):
        """Удалить старые резервные копии"""
        try:
            import pytz
            current_time = datetime.now(pytz.timezone(settings.timezone))

            for backup_file in self.backup_dir.glob("barkery_backup_*.db"):
                filename = backup_file.stem
                date_str = filename.replace("barkery_backup_", "")

                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    file_date = pytz.timezone(settings.timezone).localize(file_date)

                    age_days = (current_time - file_date).days

                    if age_days > keep_days:
                        backup_file.unlink()
                        print(f"🗑 Удалена старая резервная копия: {backup_file.name} ({age_days} дней)")

                except ValueError:
                    continue

        except Exception as e:
            print(f"⚠️ Ошибка при очистке старых бэкапов: {e}")

    def get_backup_list(self):
        """Получить список всех резервных копий"""
        backups = []
        for backup_file in self.backup_dir.glob("barkery_backup_*.db"):
            try:
                filename = backup_file.stem
                date_str = filename.replace("barkery_backup_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                file_size = os.path.getsize(backup_file) / 1024  # KB

                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size_kb': file_size,
                    'created': file_date
                })
            except ValueError:
                continue

        # Сортируем по дате (новые сверху)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups


# Создаем глобальные экземпляры для импорта
backup_manager = DatabaseBackup()


async def backup_database():
    """Функция для обратной совместимости"""
    return await backup_manager.create_backup()


print("✅ Backup manager инициализирован")