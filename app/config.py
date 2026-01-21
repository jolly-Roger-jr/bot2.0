# app/config.py
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_id: int = int(os.getenv("ADMIN_ID", "0"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barkery.db")
    timezone: str = os.getenv("TIMEZONE", "Europe/Belgrade")

    class Config:
        env_file = ".env"


settings = Settings()