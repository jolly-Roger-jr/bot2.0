"""
Barkery Shop - Версия для PythonAnywhere
Простая точка входа, которая инициализирует бота при запуске
"""
import asyncio
import logging
import sys
import os

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные
_bot = None
_dp = None
_app = None

async def init_bot():
    """Инициализирует бота (вызывается один раз)"""
    global _bot, _dp, _app
    
    from aiohttp import web
    from aiogram import Bot, Dispatcher
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    
    from config import settings
    from database import init_db
    from admin import admin_router
    from handlers import router as main_router
    
    logger.info("🚀 Barkery Shop - Инициализация для PythonAnywhere")
    
    # Проверяем настройки
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"❌ Ошибка конфигурации: {e}")
        raise
    
    # Инициализация бота
    _bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    _dp = Dispatcher()
    
    # Включаем роутеры
    _dp.include_router(admin_router)
    _dp.include_router(main_router)
    
    # Инициализация БД
    await init_db()
    
    logger.info(f"👑 Админ ID: {settings.admin_id}")
    
    # Создаем aiohttp приложение
    _app = web.Application()
    
    # Настраиваем webhook если указан хост
    if settings.webhook_host:
        webhook_url = f"{settings.webhook_url}{settings.webhook_path}"
        logger.info(f"🌐 Устанавливаю webhook: {webhook_url}")
        await _bot.set_webhook(webhook_url)
        SimpleRequestHandler(dispatcher=_dp, bot=_bot).register(_app, path=settings.webhook_path)
    else:
        logger.warning("⚠️ WEBHOOK_HOST не указан, webhook не будет работать")
    
    setup_application(_app, _dp, bot=_bot)
    
    logger.info("✅ Бот инициализирован и готов к работе")
    return _app

def get_application():
    """Возвращает приложение для WSGI"""
    global _app
    
    if _app is None:
        # Инициализируем бота при первом вызове
        logger.info("🔄 Первая инициализация приложения")
        try:
            # Создаем новый event loop для инициализации
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _app = loop.run_until_complete(init_bot())
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации: {e}")
            # Создаем простое приложение с ошибкой
            from aiohttp import web
            _app = web.Application()
            
            async def error_handler(request):
                return web.Response(text=f"Ошибка инициализации бота: {e}", status=500)
            
            _app.router.add_get('/', error_handler)
            _app.router.add_post('/', error_handler)
    
    return _app

# Объект application для PythonAnywhere
application = get_application()

# Для локального тестирования
if __name__ == "__main__":
    from aiohttp import web
    
    async def main():
        app = await init_bot()
        return app
    
    # Запускаем локально для тестирования
    web.run_app(asyncio.run(main()), host="127.0.0.1", port=8080)
