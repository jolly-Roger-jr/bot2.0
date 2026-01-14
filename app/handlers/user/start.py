# app/handlers/user/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from app.keyboards.user import categories_keyboard
from app.handlers.user.constants import WELCOME_TEXT

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    kb = categories_keyboard()
    await message.answer(WELCOME_TEXT, reply_markup=kb)