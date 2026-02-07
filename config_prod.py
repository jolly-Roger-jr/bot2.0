"""
Конфигурация для продакшена
"""
import os
from dotenv import load_dotenv

# Загружаем .env.production для продакшена
env_file = ".env.production" if os.path.exists(".env.production") else ".env"
load_dotenv(env_file)


class ProductionSettings:
    # Основные настройки
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/barkery.db")
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Belgrade")

    # Настройки бекапов
    BACKUP_DIR = os.getenv("BACKUP_DIR", "./backups")
    MAX_BACKUPS = int(os.getenv("MAX_BACKUPS", 30))

    # Настройки логирования
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

    # Валидация настроек
    @classmethod
    def validate(cls):
        errors = []

        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "ваш_токен_бота_от_BotFather":
            errors.append("BOT_TOKEN не настроен")

        if cls.ADMIN_ID == 0:
            errors.append("ADMIN_ID не настроен")

        if errors:
            raise ValueError(f"Ошибки конфигурации: {', '.join(errors)}")

        return True

    @classmethod
    def get_info(cls):
        """Информация о конфигурации"""
        return {
            "environment": cls.ENVIRONMENT,
            "database": cls.DATABASE_URL,
            "backup_dir": cls.BACKUP_DIR,
            "max_backups": cls.MAX_BACKUPS,
            "admin_id": cls.ADMIN_ID
        }


# Экспортируем настройки
settings = ProductionSettings()

# Проверяем настройки при импорте
if __name__ != "__main__":
    try:
        settings.validate()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        print("⚠️ Проверьте файл .env.production")
        exit(1)