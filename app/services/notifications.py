from aiogram import Bot
from app.config import ADMIN_ID

async def notify_admin(bot: Bot, text: str):
    await bot.send_message(ADMIN_ID, text)