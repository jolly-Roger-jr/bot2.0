# app/handlers/user/start.py
import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from app.services import catalog
from app.keyboards.user import categories_keyboard

logger = logging.getLogger(__name__)
router = Router()

WELCOME_TEXT = "Добро пожаловать! Выберите категорию:"


@router.message(CommandStart())
async def start(message: Message):
    """
    Обработчик /start — сразу показывает категории.
    """
    # Получаем категории из сервиса
    categories = await catalog.get_categories()
    kb = await categories_keyboard(categories)
    await message.answer(WELCOME_TEXT, reply_markup=kb)