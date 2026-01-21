#!/usr/bin/env python3
"""
Запуск всех тестов Barkery_bot
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Главная функция"""
    print("🧪 Запуск тестов Barkery_bot")
    print("=" * 50)
    
    try:
        import pytest
        
        # Аргументы для pytest
        args = [
            "tests/",
            "-v",  # Подробный вывод
            "--tb=short",  # Короткий traceback
            "--asyncio-mode=auto",  # Авторежим для asyncio
            "--disable-warnings",  # Отключить предупреждения для чистого вывода
        ]
        
        print(f"Запуск pytest с аргументами: {' '.join(args)}")
        print("-" * 50)
        
        # Запускаем pytest
        exit_code = pytest.main(args)
        
        print("=" * 50)
        if exit_code == 0:
            print("🎉 Все тесты прошли успешно!")
        else:
            print(f"❌ Тесты завершились с кодом: {exit_code}")
        
        return exit_code
        
    except ImportError as e:
        print(f"❌ Ошибка импорта pytest: {e}")
        print("\nУстановите pytest:")
        print("   pip install pytest pytest-asyncio")
        return 1
    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())