from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.services import catalog
from app.keyboards.user import categories_keyboard

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    categories = await catalog.get_categories()
    await message.answer(
        "🐶 Barkery Shop\nВыберите категорию:",
        reply_markup=categories_keyboard(categories)
    )