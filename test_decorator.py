print("🔍 Тестируем декораторы aiogram 3.x...")

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

# Способ 1: Через декоратор (может не работать)
router = Router()

@router.message(CommandStart())
async def handler1(message: Message):
    pass

print(f"Способ 1 (декоратор): {len(list(router.message.handlers))} хендлеров")

# Способ 2: Через register (всегда работает)
router2 = Router()

async def handler2(message: Message):
    pass

router2.message.register(handler2, CommandStart())
print(f"Способ 2 (register): {len(list(router2.message.handlers))} хендлеров")
