# app/handlers/user/back.py

from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(lambda c: c.data == "back")
async def back_handler(callback: CallbackQuery):
    """Обработчик кнопки "Назад" """
    await callback.answer("Возврат...")