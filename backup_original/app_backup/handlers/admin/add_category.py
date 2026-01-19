# app/handlers/admin/add_category.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from sqlalchemy import select  # ✅ Добавлен импорт

from app.config import settings
from app.db.session import get_session
from app.db.models import Category
from app.keyboards.admin import back_to_admin_menu

router = Router()


class AddCategoryForm(StatesGroup):
    """Состояния для добавления категории"""
    waiting_name = State()


@router.message(Command("add_category"))
async def start_add_category(message: Message, state: FSMContext):
    """Начало процесса добавления категории"""
    if str(message.from_user.id) != str(settings.admin_id):
        return

    await state.set_state(AddCategoryForm.waiting_name)

    await message.answer(
        "📂 <b>Добавление новой категории</b>\n\n"
        "Введите название категории:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:back")]
            ]
        )
    )


@router.message(AddCategoryForm.waiting_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Введите еще раз:")
        return

    # Сохраняем категорию в БД
    async for session in get_session():
        # Проверяем, нет ли уже такой категории
        result = await session.execute(
            select(Category).where(Category.name == name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            await message.answer(
                f"❌ Категория '{name}' уже существует!",
                reply_markup=back_to_admin_menu()
            )
            await state.clear()
            return

        # Создаем новую категорию
        category = Category(name=name)
        session.add(category)
        await session.commit()

    await message.answer(
        f"✅ <b>Категория '{name}' успешно добавлена!</b>\n"
        f"🆔 ID категории: {category.id}",
        parse_mode="HTML",
        reply_markup=back_to_admin_menu()
    )

    await state.clear()