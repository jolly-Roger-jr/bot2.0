#!/usr/bin/env python3
"""Тест greenlet библиотеки"""

try:
    import greenlet
    print(f"✅ greenlet установлен: {greenlet.__version__}")
except ImportError as e:
    print(f"❌ greenlet не установлен: {e}")
    print("Установите: pip install greenlet")

try:
    from sqlalchemy.ext.asyncio import create_async_engine
    print("✅ SQLAlchemy async работает")
except Exception as e:
    print(f"❌ SQLAlchemy async ошибка: {e}")
