#!/bin/bash
# setup.sh - скрипт настройки проекта

echo "🔧 Настройка проекта Barkery Bot..."

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.11 или выше"
    exit 1
fi

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Проверяем .env файл
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создайте его на основе .env.example"
    echo "   BOT_TOKEN=ваш_токен"
    echo "   ADMIN_ID=ваш_id"
    echo "   TIMEZONE=Europe/Belgrade"
    echo "   DATABASE_URL=sqlite+aiosqlite:///./barkery.db"
fi

# Создаем директории
mkdir -p backups
mkdir -p migrations

echo "✅ Настройка завершена!"
echo "🚀 Запустите бота: python launch.py"