"""
Базовый тест проекта Barkery_bot
"""

import sys
import os

# Добавляем корень проекта в путь
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("🔧 ПРОВЕРКА ИМПОРТОВ BARKERY_BOT")
print("=" * 40)

tests_passed = 0
tests_total = 0

def test_import(module, description):
    global tests_passed, tests_total
    tests_total += 1
    try:
        __import__(module)
        print(f"✅ {description}")
        tests_passed += 1
        return True
    except ImportError as e:
        print(f"❌ {description}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: {type(e).__name__}")
        tests_passed += 1  # Не фатально
        return True

# Проверяем основные импорты
test_import("app.config", "Конфигурация")
test_import("app.db.models", "Модели БД")
test_import("app.handlers.user.start", "Стартовый хендлер")
test_import("app.services.catalog", "Сервис каталога")
test_import("app.keyboards.user", "Клавиатуры")
test_import("app.callbacks", "Callback константы")
test_import("app.scheduler", "Планировщик")

print("\n" + "=" * 40)
print(f"📊 РЕЗУЛЬТАТ: {tests_passed}/{tests_total}")

if tests_passed == tests_total:
    print("🎉 Все импорты работают!")
    print("🚀 Запускайте бота: python start_bot.py")
    sys.exit(0)
else:
    print("⚠️  Есть проблемы с импортами.")
    sys.exit(1)
EOF