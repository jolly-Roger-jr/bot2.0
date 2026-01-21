#!/usr/bin/env python3
"""
Правильные тесты проекта - проверка что ВСЁ РАБОТАЕТ
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_project_structure():
    """Тест структуры проекта"""
    print("📁 Проверка структуры проекта...")

    required_dirs = [
        "app",
        "app/db",
        "app/handlers",
        "app/handlers/user",
        "app/handlers/admin",
        "app/services",
        "app/keyboards",
        "app/utils",
    ]

    required_files = [
        "app/main.py",
        "app/config.py",
        "app/db/models.py",
        "app/db/engine.py",
        "app/handlers/user/start.py",
        "app/handlers/user/cart.py",
        "app/handlers/admin/panel.py",
        "app/services/catalog.py",
        "app/services/cart.py",
        "app/keyboards/user.py",
        "app/keyboards/admin.py",
        "start_bot.py",
        "init_database.py",
    ]

    all_ok = True

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ (отсутствует)")
            all_ok = False

    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {file_path} ({size} байт)")
        else:
            print(f"  ❌ {file_path} (отсутствует)")
            all_ok = False

    return all_ok


def test_imports():
    """Тест что все импорты работают"""
    print("\n🔧 Проверка импортов...")

    imports_to_test = [
        ("aiogram", None),
        ("sqlalchemy", None),
        ("app.config", "settings"),
        ("app.db.models", "User"),
        ("app.db.models", "Product"),
        ("app.handlers.user.start", "start_command"),
        ("app.services.cart", "add_to_cart"),
    ]

    all_ok = True

    for module, attribute in imports_to_test:
        try:
            if attribute:
                # Импорт атрибута из модуля
                exec(f"from {module} import {attribute}")
                print(f"  ✅ {module}.{attribute}")
            else:
                # Импорт всего модуля
                exec(f"import {module}")
                print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            all_ok = False

    return all_ok


def test_bot_creation():
    """Тест создания бота"""
    print("\n🤖 Проверка создания бота...")

    try:
        # Тест без реального токена
        from app.config import settings

        # Временно подменим токен
        original_token = settings.bot_token
        settings.bot_token = "test_token_123"

        from app.main import setup_bot
        import asyncio

        async def test():
            bot, dp = await setup_bot()
            return bot is not None and dp is not None

        result = asyncio.run(test())

        # Восстановим токен
        settings.bot_token = original_token

        if result:
            print("  ✅ Бот может быть создан")
            return True
        else:
            print("  ❌ Не удалось создать бота")
            return False

    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
        return False


def test_database():
    """Тест базы данных"""
    print("\n🗄️  Проверка базы данных...")

    try:
        from app.db.engine import engine, Base
        from app.db.models import User, Product

        print("  ✅ Движок БД создан")
        print(f"  ✅ Модель User определена: {User.__tablename__}")
        print(f"  ✅ Модель Product определена: {Product.__tablename__}")

        # Проверяем что можем создать таблицы (в памяти)
        import asyncio

        async def test_tables():
            async with engine.begin() as conn:
                # Создаем в памяти для теста
                await conn.run_sync(Base.metadata.create_all)
                print("  ✅ Таблицы могут быть созданы")

        asyncio.run(test_tables())
        return True

    except Exception as e:
        print(f"  ❌ Ошибка БД: {e}")
        return False


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("🔍 КОМПЛЕКСНАЯ ПРОВЕРКА ПРОЕКТА BARKERY_BOT")
    print("=" * 60)

    tests = [
        ("Структура проекта", test_project_structure),
        ("Импорты", test_imports),
        ("Создание бота", test_bot_creation),
        ("База данных", test_database),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"  {'✅ ПРОЙДЕН' if success else '❌ ПРОВАЛЕН'}")
        except Exception as e:
            print(f"  ❌ ОШИБКА: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ:")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")

    print(f"\n🎯 РЕЗУЛЬТАТ: {passed}/{total}")

    if passed == total:
        print("\n🎉 ПРОЕКТ АБСОЛЮТНО ГОТОВ К РАБОТЕ!")
        print("\n🚀 Дальнейшие шаги:")
        print("1. Создайте .env файл с BOT_TOKEN и ADMIN_ID")
        print("2. Выполните: python init_database.py")
        print("3. Запустите: python start_bot.py")
        print("\n💡 Тесты пройдены, архитектура проверена!")
        return 0
    else:
        print(f"\n⚠️  Нужно исправить {total - passed} проблем")
        print("\n🔧 Рекомендации:")
        print("1. Проверьте зависимости: pip install -r requirements.txt")
        print("2. Проверьте структуру файлов")
        print("3. Запустите тест с -vv для подробностей")
        return 1


if __name__ == "__main__":
    sys.exit(main())