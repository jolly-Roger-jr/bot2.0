#!/usr/bin/env python3
"""
Чеклист для проверки готовности к деплою на PythonAnywhere
"""
import sys
import os

def check_requirements():
    """Проверка требований"""
    print("🔍 Проверка требований...")
    
    checks = []
    
    # 1. Проверка Python версии
    version = sys.version_info
    checks.append((
        f"Python {version.major}.{version.minor}.{version.micro}",
        version.major == 3 and version.minor >= 8,
        ">= 3.8"
    ))
    
    # 2. Проверка наличия файлов
    required_files = [
        ('requirements.txt', 'Файл зависимостей'),
        ('config.py', 'Конфигурация'),
        ('wsgi.py', 'WSGI точка входа'),
        ('barkery_pythonanywhere.py', 'Версия для PythonAnywhere'),
        ('database.py', 'База данных'),
    ]
    
    for file, desc in required_files:
        exists = os.path.exists(file)
        checks.append((f"{desc} ({file})", exists, "существует"))
    
    return checks

def check_config():
    """Проверка конфигурации"""
    print("\n🔧 Проверка конфигурации...")
    
    try:
        from config import settings
        
        checks = []
        checks.append(("BOT_TOKEN", bool(settings.bot_token) and settings.bot_token != "ваш_токен_бота_от_BotFather", "установлен"))
        checks.append(("ADMIN_ID", settings.admin_id != 0, "установлен"))
        checks.append(("WEBHOOK_PATH", settings.webhook_path == "/webhook", "/webhook"))
        
        return checks
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return []

def main():
    print("✅ ЧЕКЛИСТ ДЛЯ ДЕПЛОЯ НА PYTHONANYWHERE")
    print("=" * 50)
    
    # Проверка требований
    req_checks = check_requirements()
    
    all_passed = True
    
    for desc, passed, expected in req_checks:
        status = "✅" if passed else "❌"
        if not passed:
            all_passed = False
        print(f"{status} {desc}: {'Пройдено' if passed else f'Ожидается: {expected}'}")
    
    # Проверка конфигурации
    config_checks = check_config()
    
    for desc, passed, expected in config_checks:
        status = "✅" if passed else "❌"
        if not passed:
            all_passed = False
        print(f"{status} {desc}: {'Пройдено' if passed else f'Ожидается: {expected}'}")
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Проект готов к деплою.")
        print("\nДальнейшие шаги:")
        print("1. Загрузите файлы на PythonAnywhere")
        print("2. Настройте .env файл с вашими данными")
        print("3. Установите зависимости: pip install -r requirements.txt")
        print("4. Укажите wsgi.py в настройках веб-приложения")
    else:
        print("⚠️  НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("Исправьте отмеченные проблемы перед деплоем.")

if __name__ == "__main__":
    main()
