import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_ID", "0"))
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barkery.db")
    timezone = os.getenv("TIMEZONE", "Europe/Belgrade")
    
    # Настройки webhook для PythonAnywhere
    webhook_host = os.getenv("WEBHOOK_HOST", "")  # Будет установлен на PythonAnywhere
    webhook_path = os.getenv("WEBHOOK_PATH", "/webhook")
    webhook_port = int(os.getenv("WEBHOOK_PORT", "8080"))
    
    @property
    def webhook_url(self):
        """Полный URL для webhook"""
        if self.webhook_host:
            return f"https://{self.webhook_host}"
        return ""

    # Проверка обязательных полей
    @classmethod
    def validate(cls):
        if not cls.bot_token or cls.bot_token == "ваш_токен_бота_от_BotFather":
            raise ValueError("BOT_TOKEN не настроен")
        if cls.admin_id == 0:
            raise ValueError("ADMIN_ID не настроен")
        return True


settings = Settings()
