# app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    database_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()