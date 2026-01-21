#!/usr/bin/env python3
"""
Проверка установки зависимостей
"""
import sys


def check_package(package_name, import_name=None):
    """Проверить установку пакета"""
    if import_name is None:
        import_name = package_name.lower()  # Все импорты в нижнем регистре

    try:
        __import__(import_name)
        version = None

        # Попробуем получить версию
        try:
            module = sys.modules[import_name]
            if hasattr(module, '__version__'):
                version = module.__version__
            elif hasattr(module, 'version'):
                version = module.version
            elif hasattr(module, 'VERSION'):
                version = module.VERSION
        except:
            pass

        if version:
            print(f"✅ {package_name} {version}")
        else:
            print(f"✅ {package_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name} (импорт как {import_name}): {e}")
        return False


print("🔍 Проверка зависимостей Barkery_bot")
print("=" * 50)

# Основные зависимости (с правильными именами импорта)
packages = [
    ("aiogram", "aiogram"),
    ("aiohttp", "aiohttp"),
    ("aiosqlite", "aiosqlite"),
    ("SQLAlchemy", "sqlalchemy"),  # Импортируется как sqlalchemy
    ("APScheduler", "apscheduler"),  # Импортируется как apscheduler
    ("pytz", "pytz"),
    ("pydantic", "pydantic"),
    ("pydantic-settings", "pydantic_settings"),  # Импортируется как pydantic_settings
    ("alembic", "alembic"),
    ("python-dotenv", "dotenv"),  # Импортируется как dotenv
]

print("\n📦 Основные зависимости:")
all_ok = True
for package in packages:
    if not check_package(*package):
        all_ok = False

# Тестовые зависимости
test_packages = [
    ("pytest", "pytest"),
    ("packaging", "packaging"),
    ("pytest-asyncio", "pytest_asyncio"),
]

print("\n🧪 Тестовые зависимости:")
for package in test_packages:
    if not check_package(*package):
        all_ok = False

print("\n" + "=" * 50)
if all_ok:
    print("🎉 Все зависимости установлены!")
else:
    print("⚠️  Некоторые зависимости не установлены")
    print("\nУстановите недостающие:")
    print("  pip install sqlalchemy==2.0.25 apscheduler==3.10.4 pytz==2025.2")
    print("  pip install pydantic-settings==2.12.0 python-dotenv==1.0.1")