#!/usr/bin/env python3
"""
Настройка бота Barkery Shop
"""
import os
import sys

def setup_environment():
    """Настройка окружения"""
    print("🔧 Настройка Barkery Bot")
    print("=" * 50)
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("📄 Создаю .env из примера...")
            os.system('cp .env.example .env')
            print("✅ .env файл создан")
        else:
            print("❌ .env.example не найден!")
            return False
    
    # Читаем текущий .env
    with open('.env', 'r') as f:
        content = f.read()
    
    # Проверяем настройки
    needs_update = False
    if 'ваш_токен_бота_от_BotFather' in content:
        print("⚠️  Нужно установить BOT_TOKEN")
        print("   Получите токен у @BotFather в Telegram")
        token = input("Введите BOT_TOKEN: ").strip()
        if token:
            content = content.replace('ваш_токен_бота_от_BotFather', token)
            needs_update = True
        else:
            print("❌ Токен не введен!")
            return False
    
    if 'ваш_telegram_id_без_кавычек' in content:
        print("⚠️  Нужно установить ADMIN_ID")
        print("   Узнайте свой ID у @userinfobot в Telegram")
        admin_id = input("Введите ADMIN_ID: ").strip()
        if admin_id and admin_id.isdigit():
            content = content.replace('ваш_telegram_id_без_кавычек', admin_id)
            needs_update = True
        else:
            print("❌ ID должен быть числом!")
            return False
    
    # Сохраняем изменения
    if needs_update:
        with open('.env', 'w') as f:
            f.write(content)
        print("✅ .env файл обновлен")
    
    # Тестируем настройки
    print("\n🧪 Тестирую настройки...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        bot_token = os.getenv('BOT_TOKEN')
        admin_id = os.getenv('ADMIN_ID')
        
        if bot_token and bot_token != 'test' and 'ваш_токен' not in bot_token:
            print(f"✅ BOT_TOKEN: {'установлен'}")
        else:
            print(f"❌ BOT_TOKEN: не установлен")
            return False
            
        if admin_id and admin_id.isdigit():
            print(f"✅ ADMIN_ID: {admin_id}")
        else:
            print(f"❌ ADMIN_ID: не установлен")
            return False
        
        print("\n🎉 Все настройки корректны!")
        print("\n📋 Что дальше:")
        print("1. Запустите бота: python3 barkery_bot.py")
        print("2. Откройте Telegram и найдите вашего бота")
        print("3. Нажмите /start")
        print("4. Используйте кнопки для навигации")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    if setup_environment():
        sys.exit(0)
    else:
        sys.exit(1)
