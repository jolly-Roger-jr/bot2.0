FROM python:3.11-slim

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 -s /bin/bash barkery
USER barkery
WORKDIR /home/barkery/app

# Копируем зависимости
COPY --chown=barkery:barkery requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем структуру директорий


# Копируем исходный код
COPY --chown=barkery:barkery . .

# Настройка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Запускаем бота
CMD ["python", "barkery_bot.py"]