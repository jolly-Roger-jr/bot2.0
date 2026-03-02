#!/bin/bash
echo "🐕 Запуск Barkery Shop Bot (PRODUCTION MODE)"
echo "================================"

# Проверка .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Создаем директорию для логов если нет
mkdir -p logs

# Функция запуска бота
run_bot() {
    echo "✅ $(date): Бот запущен"
    python3 barkery_bot.py >> logs/bot.log 2>&1
}

# Бесконечный цикл с перезапуском
while true; do
    run_bot
    echo "⚠️ $(date): Бот упал, перезапуск через 5 секунд..."
    sleep 5
done
