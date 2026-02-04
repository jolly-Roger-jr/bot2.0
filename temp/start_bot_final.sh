#!/bin/bash
echo "========================================="
echo "🚀 ЗАПУСК BARKERY SHOP BOT"
echo "========================================="
echo

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo
    echo "Создайте файл .env с содержимым:"
    echo "BOT_TOKEN=ваш_токен_бота"
    echo "ADMIN_ID=ваш_telegram_id"
    echo "DATABASE_URL=sqlite+aiosqlite:///./barkery.db"
    echo
    echo "Можно скопировать пример:"
    echo "cp .env.example .env"
    echo
    exit 1
fi

# Проверяем наличие токена
if ! grep -q "BOT_TOKEN=" .env; then
    echo "❌ BOT_TOKEN не найден в .env файле"
    exit 1
fi

# Проверяем наличие зависимостей
echo "🔍 Проверка зависимостей..."
if ! pip show aiogram > /dev/null 2>&1; then
    echo "Установка зависимостей..."
    pip install -r requirements.txt
fi

# Запускаем бота
echo
echo "🚀 Запуск бота..."
echo "========================================="
python3 barkery_bot.py
