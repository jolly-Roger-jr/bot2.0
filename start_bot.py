#!/usr/bin/env python3
"""
Простой запуск бота Barkery Shop
"""
import asyncio
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

async def main():
    print("🐶 Barkery Shop - запуск бота")
    print("=" * 40)
    
    try:
        # Импортируем настройки
        from app.config import settings
        print(f"✅ Настройки загружены")
        print(f"   👑 Admin ID: {settings.admin_id}")
        print(f"   🔐 Токен: {settings.bot_token[:15]}...")
        
        # Проверяем импорт основного модуля
        from app.main import main as bot_main
        print("✅ Основной модуль загружен")
        
        print("\n🚀 Запускаем бота...")
        print("📱 Найдите @BarkeryShopBot в Telegram")
        print("📝 Отправьте /start для начала работы")
        print("⚡ Для остановки: Ctrl+C")
        print("=" * 40)
        
        # Запускаем основной бот
        await bot_main()
        
    except ImportError as e:
        print(f"\n❌ Ошибка импорта: {e}")
        print("Проверьте структуру проекта")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
