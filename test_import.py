print("🔍 Тестируем импорты aiogram...")

try:
    from aiogram import Bot, Dispatcher, Router
    print("✅ Bot, Dispatcher, Router - OK")
except ImportError as e:
    print(f"❌ Ошибка: {e}")

try:
    from aiogram.filters import CommandStart
    print("✅ CommandStart - OK")
except ImportError as e:
    print(f"❌ Ошибка: {e}")

try:
    from aiogram.types import Message
    print("✅ Message - OK")
except ImportError as e:
    print(f"❌ Ошибка: {e}")

print("\n📦 Версия aiogram:")
import aiogram
print(f"   {aiogram.__version__}")
