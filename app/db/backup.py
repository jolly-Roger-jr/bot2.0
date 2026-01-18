# app/db/backup.py

import asyncio
import aiofiles
import os
import pytz  # ДОБАВЛЕНО
from datetime import datetime
from pathlib import Path
from app.config import settings
from app.utils.timezone import get_serbia_time, format_serbia_time


class DatabaseBackup:
    """Класс для управления резервными копиями базы данных"""

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

        # Получаем путь к основной БД из DATABASE_URL
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
        self.source_db = Path(db_path)

    async def create_backup(self) -> str:
        """
        Создать резервную копию базы данных
        Возвращает путь к созданному файлу резервной копии
        """
        if not self.source_db.exists():
            raise FileNotFoundError(f"Основная БД не найдена: {self.source_db}")

        # Формируем имя файла с timestamp
        timestamp = format_serbia_time(fmt="%Y%m%d_%H%M%S")
        backup_filename = f"barkery_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        try:
            # Асинхронное копирование файла
            async with aiofiles.open(self.source_db, 'rb') as src:
                async with aiofiles.open(backup_path, 'wb') as dst:
                    content = await src.read()
                    await dst.write(content)

            # Логирование успешного копирования
            file_size = os.path.getsize(backup_path) / 1024  # размер в КБ
            print(f"✅ Резервная копия создана: {backup_path} ({file_size:.2f} KB)")

            # Очистка старых бэкапов (храним последние 7 дней)
            await self._cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            print(f"❌ Ошибка при создании резервной копии: {e}")
            raise

    async def _cleanup_old_backups(self, keep_days: int = 7):
        """Удалить старые резервные копии (старше keep_days дней)"""
        try:
            current_time = get_serbia_time()

            for backup_file in self.backup_dir.glob("barkery_backup_*.db"):
                # Извлекаем дату из имени файла
                filename = backup_file.stem
                date_str = filename.replace("barkery_backup_", "")

                try:
                    file_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    file_date = pytz.timezone(settings.timezone).localize(file_date)

                    # Проверяем возраст файла
                    age_days = (current_time - file_date).days

                    if age_days > keep_days:
                        backup_file.unlink()
                        print(f"🗑 Удалена старая резервная копия: {backup_file.name} ({age_days} дней)")

                except ValueError:
                    # Неправильный формат имени файла - пропускаем
                    continue

        except Exception as e:
            print(f"⚠️ Ошибка при очистке старых бэкапов: {e}")

    def get_backup_list(self) -> list:
        """Получить список всех резервных копий"""
        backups = []
        for backup_file in sorted(self.backup_dir.glob("barkery_backup_*.db"), reverse=True):
            file_info = {
                'name': backup_file.name,
                'path': str(backup_file),
                'size_kb': os.path.getsize(backup_file) / 1024,
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime)
            }
            backups.append(file_info)
        return backups

    async def restore_from_backup(self, backup_path: str) -> bool:
        """
        Восстановить БД из резервной копии
        ВНИМАНИЕ: Перезаписывает текущую БД!
        """
        backup_file = Path(backup_path)
        if not backup_file.exists():
            raise FileNotFoundError(f"Файл резервной копии не найден: {backup_path}")

        try:
            # Создаем резервную копию текущей БД перед восстановлением
            current_backup = await self.create_backup()
            print(f"📁 Создана резервная копия текущего состояния: {current_backup}")

            # Восстанавливаем из выбранной копии
            async with aiofiles.open(backup_file, 'rb') as src:
                async with aiofiles.open(self.source_db, 'wb') as dst:
                    content = await src.read()
                    await dst.write(content)

            print(f"✅ База данных восстановлена из: {backup_path}")
            return True

        except Exception as e:
            print(f"❌ Ошибка при восстановлении из резервной копии: {e}")
            return False


# Глобальный экземпляр для удобства использования
backup_manager = DatabaseBackup()


async def backup_database():
    """Основная функция для создания резервной копии (вызывается планировщиком)"""
    try:
        backup_path = await backup_manager.create_backup()
        return {
            'success': True,
            'path': backup_path,
            'timestamp': format_serbia_time()
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'timestamp': format_serbia_time()
        }