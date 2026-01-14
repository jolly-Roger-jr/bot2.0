from aiogram import Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command  # <-- добавлено

router = Router()

# Пример категорий
CATEGORIES = ["Мотивационные лакомства", "Погрызухи", "Гипоаллергенные лакомства"]

@router.message(Command("start"))  # <-- исправлено
async def start_handler(message: Message):
    builder = InlineKeyboardBuilder()
    for cat in CATEGORIES:
        # callback_data используем как идентификатор категории
        builder.button(text=cat, callback_data=f"cat:{cat}")
    keyboard = builder.as_markup(row_width=1)

    await message.answer(
        "🐶 Добро пожаловать в Barkery!\nВыберите категорию:",
        reply_markup=keyboard
    )