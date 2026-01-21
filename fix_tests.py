#!/usr/bin/env python3
"""
Скрипт для постепенного исправления тестов
"""
import os
import subprocess
import sys


def run_command(cmd, description):
    """Запуск команды с выводом"""
    print(f"\n🔧 {description}...")
    print(f"   $ {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"   ✅ Успешно")
            if result.stdout:
                print(f"   Вывод: {result.stdout[:200]}...")
        else:
            print(f"   ❌ Ошибка: {result.stderr}")
            return False

        return True
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False


def main():
    """Главная функция"""
    print("🛠️  Исправление тестов Barkery_bot")
    print("=" * 60)

    steps = [
        # 1. Очистка
        ("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null", "Очистка кэша"),

        # 2. Установка зависимостей
        ("pip install pytest==7.4.4", "Установка pytest"),
        ("pip install pytest-asyncio==0.21.1", "Установка pytest-asyncio"),

        # 3. Проверка импортов
        ("python -c 'import pytest; print(f\"pytest version: {pytest.__version__}\")'", "Проверка pytest"),
        ("python -c 'from app.db.models import Base; print(\"✅ Models import OK\")'", "Проверка импорта моделей"),

        # 4. Запуск минимального теста
        ("pytest tests/test_minimal.py -v", "Запуск минимальных тестов"),

        # 5. Запуск тестов моделей
        ("pytest tests/test_models.py -v", "Запуск тестов моделей"),
    ]

    success_count = 0

    for cmd, description in steps:
        if run_command(cmd, description):
            success_count += 1
        else:
            print(f"\n⚠️  Остановка на шаге: {description}")
            break

    print(f"\n{'=' * 60}")
    print(f"📊 Результат: {success_count}/{len(steps)} шагов выполнено успешно")

    if success_count == len(steps):
        print("🎉 Все тесты должны работать!")
        print("\nСледующие шаги:")
        print("1. python run_tests.py           # Запустить все тесты")
        print("2. make test                     # Или через Makefile")
    else:
        print("❌ Требуется дополнительная настройка")


if __name__ == "__main__":
    main()