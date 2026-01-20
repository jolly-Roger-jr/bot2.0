# !/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Запуск: python init_database.py
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def main():
    """Инициализация БД"""
    print("🔄 Инициализация базы данных...")

    try:
        # Создаем таблицы
        from app.db.engine import engine, Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы")

        # Добавляем тестовые данные
        from app.db.init_db import init_database
        await init_database()
        print("✅ Тестовые данные добавлены")

        print("🎯 База данных готова к работе!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())