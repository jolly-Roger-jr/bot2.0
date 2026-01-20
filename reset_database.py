#!/usr/bin/env python3
"""
Скрипт для сброса базы данных
Внимание: удаляет все данные!
Запуск: python reset_database.py
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def main():
    """Сброс БД"""
    print("⚠️  ВНИМАНИЕ: Это удалит все данные из базы!")
    response = input("Продолжить? (yes/no): ")

    if response.lower() != 'yes':
        print("❌ Отменено")
        return

    try:
        from app.db.engine import engine, Base

        # Удаляем все таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("🗑️  Все таблицы удалены")

        # Создаем заново
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы заново")

        print("🔄 База данных сброшена!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())