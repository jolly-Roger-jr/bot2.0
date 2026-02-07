FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 -s /bin/bash barkery
USER barkery
WORKDIR /home/barkery/app

# Копируем зависимости
COPY --chown=barkery:barkery requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем структуру директорий
RUN mkdir -p data backups logs

# Копируем исходный код
COPY --chown=barkery:barkery . .

# Настройка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Запускаем бота
CMD ["python", "barkery_bot.py"]