import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from keyboards import main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🐕 Добро пожаловать в Barkery Shop!\n\n"
        "Магазин натуральных собачьих лакомств 🦴",
        reply_markup=main_menu_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Помощь: @support")
