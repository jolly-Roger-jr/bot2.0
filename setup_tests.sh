#!/bin/bash
# Скрипт для установки тестовых зависимостей

echo "🔧 Установка зависимостей для тестов..."

# Проверяем наличие virtualenv
if [ ! -d "venv" ]; then
    echo "Создаю virtualenv..."
    python3 -m venv venv
fi

# Активируем virtualenv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "✅ Зависимости установлены!"
echo ""
echo "Запуск тестов:"
echo "  python run_tests.py              # Все тесты"
echo "  python run_tests.py test_models  # Только тесты моделей"
echo ""