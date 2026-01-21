#!/usr/bin/env python3
"""
Запуск всех тестов Barkery_bot с правильной конфигурацией
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_test_environment():
    """Настройка тестового окружения"""
    # Устанавливаем переменные окружения для тестов
    os.environ["TESTING"] = "1"
    os.environ["BOT_TOKEN"] = "test_token"
    os.environ["ADMIN_ID"] = "123456789"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["TIMEZONE"] = "Europe/Belgrade"

    print("🔧 Настройка тестового окружения...")
    print("   TESTING=1")
    print("   DATABASE_URL=sqlite+aiosqlite:///:memory:")
    print("   Используется in-memory база данных")


def run_tests_with_coverage():
    """Запуск тестов с покрытием"""
    try:
        import pytest

        setup_test_environment()

        print("\n🧪 Запуск тестов Barkery_bot")
        print("=" * 50)

        # Запускаем тесты поэтапно

        print("\n📋 Этап 1: Базовые тесты")
        print("-" * 30)
        exit_code1 = pytest.main([
            "tests/test_basic.py",
            "tests/test_simple_working.py",
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            "-x"  # Остановиться при первой ошибке
        ])

        if exit_code1 != 0:
            print(f"\n❌ Базовые тесты провалились: {exit_code1}")
            return exit_code1

        print("\n📋 Этап 2: Smoke тесты")
        print("-" * 30)
        exit_code2 = pytest.main([
            "tests/",
            "-k", "not backup and not integration",
            "-v",
            "--tb=short",
            "--asyncio-mode=auto",
            "--disable-warnings"
        ])

        print("\n" + "=" * 50)

        if exit_code2 == 0:
            print("🎉 Все тесты прошли успешно!")
            print("\n✅ Проект готов к работе!")
            print("\nДальнейшие шаги:")
            print("1. Создайте .env файл с реальным BOT_TOKEN")
            print("2. Запустите: python init_database.py")
            print("3. Запустите бота: python start_bot.py")
        else:
            print(f"⚠️  Некоторые тесты не прошли: {exit_code2}")

        return exit_code2

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return 1
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Главная функция"""
    return run_tests_with_coverage()


if __name__ == "__main__":
    sys.exit(main())