# app/handlers/admin/add_product.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from sqlalchemy import select  # ДОБАВЬТЕ ЭТОТ ИМПОРТ

from app.config import settings
from app.db.session import get_session
from app.db.models import Product, Category
from app.keyboards.admin import back_to_admin_menu

router = Router()

# ... остальной код из предыдущего сообщения