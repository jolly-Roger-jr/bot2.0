FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем необходимые директории
RUN mkdir -p backups remote_backups

# Инициализируем БД (если нет миграций)
RUN python -c "
import asyncio
import sys
sys.path.append('/app')
from app.db.engine import Base, engine
from app.db.models import *
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init_db())
print('✅ База данных инициализирована')
"

# Применяем миграции если они есть
RUN if [ -f alembic.ini ]; then \
    alembic upgrade head; \
    echo '✅ Миграции применены'; \
fi

# Запускаем бота
CMD ["python", "start_bot.py"]