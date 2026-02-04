#!/bin/bash

echo "🐕 Запуск Barkery Shop..."
echo "=========================="
echo ""

# Проверяем .env
if [ ! -f ".env" ]; then
    echo "❌ Ошибка: Файл .env не найден"
    echo "Создайте .env с содержимым:"
    echo "BOT_TOKEN=your_bot_token_here"
    echo "ADMIN_ID=123456789"
    echo "DATABASE_URL=sqlite+aiosqlite:///./barkery.db"
    echo "TIMEZONE=Europe/Belgrade"
    exit 1
fi

# Проверяем токен бота
if grep -q "BOT_TOKEN=your_bot_token_here" .env; then
    echo "⚠️  Внимание: BOT_TOKEN не настроен в .env"
    echo "Исправьте файл .env перед запуском"
    exit 1
fi

# Создаем директорию для логов
mkdir -p logs

echo "✅ Конфигурация проверена"
echo "⏳ Запуск бота..."

# Запускаем бота с логированием
python barkery_bot.py 2>&1 | tee "logs/bot_$(date +%Y%m%d_%H%M%S).log"

echo ""
echo "🛑 Бот остановлен"
