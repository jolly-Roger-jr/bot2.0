import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    bot_token = os.getenv("BOT_TOKEN")
    admin_id = int(os.getenv("ADMIN_ID", "0"))
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barkery.db")
    timezone = os.getenv("TIMEZONE", "Europe/Belgrade")

    # Проверка обязательных полей
    @classmethod
    def validate(cls):
        if not cls.bot_token or cls.bot_token == "ваш_токен_бота_от_BotFather":
            raise ValueError("BOT_TOKEN не настроен")
        if cls.admin_id == 0:
            raise ValueError("ADMIN_ID не настроен")
        return True


settings = Settings()