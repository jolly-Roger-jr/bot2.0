#!/usr/bin/env python3
"""
Запуск простых тестов для проверки установки
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_basic_tests():
    """Запуск базовых тестов"""
    print("🧪 Запуск базовых тестов установки")
    print("=" * 50)

    tests = [
        ("test_imports", "Импорт зависимостей"),
        ("test_project_structure", "Структура проекта"),
        ("test_models_simple", "Модели БД"),
    ]

    success_count = 0

    for test_func, description in tests:
        try:
            # Импортируем и запускаем тест
            from tests.test_basic import test_imports, test_project_structure, test_models_simple

            if test_func == "test_imports":
                test_imports()
            elif test_func == "test_project_structure":
                test_project_structure()
            elif test_func == "test_models_simple":
                test_models_simple()

            print(f"✅ {description}")
            success_count += 1
        except Exception as e:
            print(f"❌ {description}: {e}")

    print(f"\n📊 Результат: {success_count}/{len(tests)} тестов прошли")

    if success_count == len(tests):
        print("🎉 Базовая установка успешна!")
        print("\nДальнейшие шаги:")
        print("1. Создайте .env файл")
        print("2. Выполните: python init_database.py")
        print("3. Запустите бота: python start_bot.py")
        return 0
    else:
        print("⚠️  Требуется исправление зависимостей")
        return 1


if __name__ == "__main__":
    sys.exit(run_basic_tests())