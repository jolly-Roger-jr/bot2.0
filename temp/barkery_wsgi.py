#!/usr/bin/env python3
"""
Barkery Shop - WSGI версия для PythonAnywhere
"""
import asyncio
import logging
import sys
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from database import init_db
from admin import admin_router
from handlers import router as main_router

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для бота и диспетчера
bot = None
dp = None

async def on_startup(dispatcher: Dispatcher, bot: Bot):
    """Действия при запуске бота"""
    await bot.set_webhook(f"{settings.webhook_url}{settings.webhook_path}")
    logger.info("Webhook установлен")

async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    """Действия при остановке бота"""
    await bot.delete_webhook()
    logger.info("Webhook удален")

async def init_bot():
    """Инициализация бота (асинхронная)"""
    global bot, dp
    
    logger.info("🚀 Barkery Shop - Инициализация бота для PythonAnywhere")
    
    try:
        # Проверяем настройки
        settings.validate()
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        sys.exit(1)
    
    # Инициализация бота
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Настраиваем webhook
    dp["webhook_url"] = settings.webhook_url
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Включаем роутеры
    dp.include_router(admin_router)
    dp.include_router(main_router)
    
    # Инициализация БД
    await init_db()
    
    logger.info(f"👑 Админ ID: {settings.admin_id}")
    logger.info(f"🌐 Webhook URL: {settings.webhook_url}{settings.webhook_path}")
    logger.info("✅ Бот инициализирован для работы через webhook")
    
    return dp, bot

# Создаем aiohttp приложение
app = web.Application()

# Инициализируем бота при запуске WSGI
async def setup_bot(app):
    """Настройка бота при запуске приложения"""
    dp, bot = await init_bot()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    return app

# Запускаем инициализацию
if __name__ == "__main__":
    # Это для локального тестирования
    from aiohttp import web
    import asyncio
    
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(setup_bot(web.Application()))
    
    web.run_app(app, host="127.0.0.1", port=8080)
else:
    # Это для PythonAnywhere
    import asyncio
    
    # Создаем новый event loop для WSGI
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Инициализируем приложение
    app = loop.run_until_complete(setup_bot(web.Application()))
