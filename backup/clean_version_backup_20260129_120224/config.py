import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    bot_token = os.getenv("BOT_TOKEN", "test")
    admin_id = int(os.getenv("ADMIN_ID", "123456789"))
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barkery.db")
    timezone = os.getenv("TIMEZONE", "Europe/Belgrade")

settings = Settings()
