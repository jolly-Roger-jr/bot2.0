#!/usr/bin/env python3
"""
Запуск Barkery_bot - оптимизированная версия
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def main():
    """Основная функция запуска"""
    print("=" * 50)
    print("🚀 Barkery Bot - Запуск...")
    print("=" * 50)

    try:
        from app.main import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        print("\n👋 Завершение работы")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())