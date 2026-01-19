# real_bot.py
import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🤖 ЗАПУСК БОТА С РЕАЛЬНЫМ ТОКЕНОМ")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


async def main():
    try:
        # 1. Загружаем настройки
        from app.config import settings

        print(f"🔧 Загружены настройки:")
        print(f"   Admin ID: {settings.admin_id}")
        print(f"   Timezone: {settings.timezone}")

        # Проверяем токен
        token = settings.bot_token
        if not token:
            logger.error("❌ Токен бота не найден в .env файле!")
            print("Добавьте в .env: BOT_TOKEN=ваш_токен")
            return

        if len(token) < 30:
            logger.error(f"❌ Токен слишком короткий: {len(token)} символов")
            print("Проверьте правильность токена в .env файле")
            return

        print(f"   Токен: {'*' * 20}{token[-6:]}")

        # 2. Импортируем aiogram
        from aiogram import Bot, Dispatcher, Router, F
        from aiogram.filters import CommandStart, Command
        from aiogram.types import Message, ReplyKeyboardRemove
        from aiogram.fsm.storage.memory import MemoryStorage

        print("✅ AIOGRAM импортирован")

        # 3. Создаем бота
        try:
            bot = Bot(token=token)
            print("✅ Bot объект создан")
        except Exception as e:
            logger.error(f"❌ Ошибка создания Bot: {e}")
            print("Проверьте токен в .env файле")
            return

        # 4. Создаем диспетчер и роутер
        dp = Dispatcher(storage=MemoryStorage())
        router = Router()

        print("📝 Регистрируем хендлеры...")

        # Хендлер 1: /start
        @router.message(CommandStart())
        async def cmd_start(message: Message):
            await message.answer(
                "🐶 <b>Barkery Shop - Магазин натуральных лакомств для собак</b>\n\n"
                "Добро пожаловать! Используйте команды:\n"
                "/start - это сообщение\n"
                "/help - помощь\n"
                "/test - тест бота\n\n"
                "<i>Работаем 24/7! 🐾</i>",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"User {message.from_user.id} used /start")

        # Хендлер 2: /help
        @router.message(Command("help"))
        async def cmd_help(message: Message):
            await message.answer(
                "ℹ️ <b>Помощь по командам:</b>\n\n"
                "/start - Главное меню\n"
                "/help - Эта справка\n"
                "/test - Тест работы бота\n"
                "/admin - Админ-панель\n\n"
                "<i>Скоро будет каталог товаров и корзина!</i>",
                parse_mode="HTML"
            )

        # Хендлер 3: /test
        @router.message(Command("test"))
        async def cmd_test(message: Message):
            await message.answer(
                "✅ <b>Бот работает исправно!</b>\n\n"
                "Все системы в норме. 🚀",
                parse_mode="HTML"
            )
            logger.info(f"Test command from {message.from_user.id}")

        # Хендлер 4: ping
        @router.message(F.text.lower() == "ping")
        async def cmd_ping(message: Message):
            await message.answer("🏓 Pong!")

        # Хендлер 5: echo (для теста)
        @router.message(F.text)
        async def echo(message: Message):
            if message.text.startswith('/'):
                return  # Игнорируем команды
            await message.answer(f"📝 Вы написали: {message.text}")

        # 5. Включаем роутер
        dp.include_router(router)

        # 6. Проверяем хендлеры ДО запуска
        handlers = list(dp.message.handlers)
        logger.info(f"📊 Зарегистрировано хендлеров: {len(handlers)}")

        if len(handlers) == 0:
            logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА: Хендлеры не зарегистрированы!")
            print("\nВозможные решения:")
            print("1. Проверьте импорты в начале файла")
            print("2. Убедитесь что декораторы @router.message правильно написаны")
            print("3. Проверьте нет ли синтаксических ошибок в коде")
            return

        print("✅ Все хендлеры зарегистрированы")
        print(f"   Команды: /start, /help, /test, ping")

        # 7. Запускаем планировщик если есть
        try:
            from app.scheduler import setup_backup_schedule, start_scheduler
            setup_backup_schedule()
            start_scheduler()
            print("✅ Планировщик резервного копирования запущен")
        except:
            print("⚠️  Планировщик не подключен (это нормально для теста)")

        # 8. Запускаем бота
        print("\n" + "=" * 50)
        print("🚀 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
        print("=" * 50)
        print("\nОтправьте в Telegram боту:")
        print("✅ /start - для начала работы")
        print("✅ /test - для проверки")
        print("✅ ping - для теста")
        print("\nДля остановки нажмите Ctrl+C")

        await dp.start_polling(bot)

    except ImportError as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        print("\nПроверьте установлены ли все зависимости:")
        print("pip install aiogram pydantic python-dotenv")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Завершение работы бота")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹ Остановлено пользователем")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")