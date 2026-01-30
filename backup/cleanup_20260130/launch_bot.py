#!/usr/bin/env python3
"""
Запуск Barkery Bot с проверками
"""
import os
import sys
import subprocess
import time

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import aiogram
        print(f"✅ aiogram {aiogram.__version__}")
    except ImportError:
        print("❌ aiogram не установлен")
        return False
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy {sqlalchemy.__version__}")
    except ImportError:
        print("❌ SQLAlchemy не установлен")
        return False
    
    try:
        import dotenv
        print(f"✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv не установлен")
        return False
    
    return True

def check_config():
    """Проверка конфигурации"""
    print("\n🔧 Проверка конфигурации...")
    
    if not os.path.exists(".env"):
        print("❌ Файл .env не найден")
        if os.path.exists(".env.example"):
            print("ℹ️  Копирую .env.example в .env...")
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Создан файл .env из примера")
            print("⚠️  Нужно отредактировать .env и указать BOT_TOKEN и ADMIN_ID")
            return False
        else:
            print("❌ Файл .env.example также не найден")
            return False
    
    # Читаем .env
    with open(".env", "r") as f:
        content = f.read()
    
    issues = []
    if "ваш_токен" in content or "test" in content:
        issues.append("❌ BOT_TOKEN не установлен")
    
    if "ваш_telegram_id" in content or "123456789" in str(content):
        issues.append("❌ ADMIN_ID не установлен")
    
    if issues:
        print("\n".join(issues))
        print("\n📝 Отредактируйте файл .env:")
        print("   BOT_TOKEN=ваш_токен_от_BotFather")
        print("   ADMIN_ID=ваш_id_в_telegram")
        return False
    
    print("✅ Конфигурация в порядке")
    return True

def check_database():
    """Проверка базы данных"""
    print("\n🗄️  Проверка базы данных...")
    
    try:
        from database import init_db
        print("✅ Модели БД загружены")
        
        # Проверим структуру
        from database import Product
        required_fields = ['unit_type', 'measurement_step', 'image_url']
        
        for field in required_fields:
            if hasattr(Product, field):
                print(f"✅ Поле {field} существует")
            else:
                print(f"❌ Поле {field} отсутствует")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

def main():
    print("🚀 Barkery Bot - Лаунчер")
    print("=" * 60)
    
    # Проверяем все
    if not check_dependencies():
        print("\n⚠️  Установите зависимости: pip install -r requirements.txt")
        sys.exit(1)
    
    if not check_config():
        print("\n⚠️  Настройте конфигурацию в файле .env")
        sys.exit(1)
    
    if not check_database():
        print("\n⚠️  Проблемы с базой данных")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print("\n🎯 Функционал бота:")
    print("   📦 Каталог с категориями и товарами")
    print("   🛒 Корзина с кнопками +/- (граммы/штуки)")
    print("   🛎️  Оформление заказа с уведомлением админу")
    print("   👑 Админка (/admin):")
    print("     • Управление категориями (добавление/редактирование/удаление)")
    print("     • Управление товарами (добавление/редактирование/удаление)")
    print("     • Загрузка изображений товаров")
    print("     • Установка единиц измерения (граммы/штуки)")
    
    print("\n🚀 Запуск бота...")
    print("=" * 60)
    
    try:
        # Запускаем основной файл бота
        subprocess.run([sys.executable, "barkery_bot.py"])
    except KeyboardInterrupt:
        print("\n⏹️  Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
