#!/usr/bin/env python3
"""
Простой тест для проверки работоспособности
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Тест импортов"""
    print("🧪 Тестирование импортов...")

    try:
        # Импорт моделей
        from app.db.models import Base, User, Category, Product
        print("✅ Модели БД импортированы")

        # Импорт конфигурации
        from app.config import settings
        print("✅ Конфигурация импортирована")

        # Импорт сервисов
        from app.services.catalog import get_categories
        print("✅ Сервисы импортированы")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_imports():
    """Тест асинхронных импортов"""
    print("\n🧪 Тестирование асинхронных импортов...")

    try:
        # Импорт асинхронных компонентов
        from app.db.engine import engine
        print("✅ Асинхронный движок БД импортирован")

        return True
    except Exception as e:
        print(f"❌ Ошибка асинхронного импорта: {e}")
        return False


def main():
    """Главная функция"""
    print("🚀 Запуск проверки Barkery_bot")
    print("=" * 50)

    # Тест синхронных импортов
    sync_ok = test_imports()

    # Тест асинхронных импортов
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async_ok = loop.run_until_complete(test_async_imports())
        loop.close()
    except:
        async_ok = False

    print("\n" + "=" * 50)
    if sync_ok and async_ok:
        print("🎉 Все импорты работают!")
        print("\nСледующие шаги:")
        print("1. Создайте .env файл с BOT_TOKEN")
        print("2. Запустите: python start_bot.py")
        print("3. Протестируйте команду /start")
        return 0
    else:
        print("❌ Есть проблемы с импортами")
        return 1


if __name__ == "__main__":
    sys.exit(main())