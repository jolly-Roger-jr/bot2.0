# app/handlers/user/cart.py
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text == "/cart")
async def show_cart(message: Message):
    await message.answer("Ваша корзина пуста.")