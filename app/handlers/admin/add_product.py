# app/handlers/admin/add_product.py - ИСПРАВЛЕННЫЙ

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from sqlalchemy import select

from app.config import settings
from app.db.session import get_session
from app.db.models import Product, Category
from app.keyboards.admin import back_to_admin_menu

router = Router()


class AddProductForm(StatesGroup):
    """Состояния для добавления товара"""
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_category = State()
    waiting_stock = State()


@router.message(Command("add_product"))
async def start_add_product(message: Message, state: FSMContext):
    """Начало процесса добавления товара"""
    if str(message.from_user.id) != str(settings.admin_id):
        return

    # Получаем список категорий
    async for session in get_session():
        result = await session.execute(select(Category))
        categories = result.scalars().all()

    if not categories:
        await message.answer(
            "❌ Сначала нужно создать категории через /add_category",
            reply_markup=back_to_admin_menu()
        )
        return

    # Сохраняем категории в состоянии
    await state.update_data(categories=categories)
    await state.set_state(AddProductForm.waiting_name)

    await message.answer(
        "➕ <b>Добавление нового товара</b>\n\n"
        "Введите название товара:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:back")]
            ]
        )
    )


@router.message(AddProductForm.waiting_name)
async def process_product_name(message: Message, state: FSMContext):
    """Обработка названия товара"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Введите еще раз:")
        return

    await state.update_data(name=name)
    await state.set_state(AddProductForm.waiting_description)

    await message.answer(
        "📝 Теперь введите описание товара:\n"
        "<i>Можно оставить пустым, отправьте '-'</i>",
        parse_mode="HTML"
    )


@router.message(AddProductForm.waiting_description)
async def process_product_description(message: Message, state: FSMContext):
    """Обработка описания товара"""
    description = message.text.strip()
    if description == "-":
        description = None

    await state.update_data(description=description)
    await state.set_state(AddProductForm.waiting_price)

    await message.answer(
        "💰 Введите цену за 100 грамм (в RSD):\n"
        "<i>Например: 150.50</i>",
        parse_mode="HTML"
    )


@router.message(AddProductForm.waiting_price)
async def process_product_price(message: Message, state: FSMContext):
    """Обработка цены товара"""
    try:
        price = float(message.text.strip().replace(',', '.'))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число:")
        return

    await state.update_data(price=price)
    await state.set_state(AddProductForm.waiting_category)

    # Показываем доступные категории
    data = await state.get_data()
    categories = data.get('categories', [])

    if not categories:
        await message.answer("❌ Категории не найдены. Начните заново.")
        await state.clear()
        return

    # Создаем клавиатуру с категориями
    buttons = []
    for category in categories:
        buttons.append([
            InlineKeyboardButton(
                text=category.name,
                callback_data=f"add_product:category:{category.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="admin:back")])

    await message.answer(
        "📂 Выберите категорию товара:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith("add_product:category:"))
async def process_product_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    category_id = int(callback.data.split(":")[2])
    await state.update_data(category_id=category_id)
    await state.set_state(AddProductForm.waiting_stock)

    await callback.message.edit_text(
        "📦 Введите начальное количество товара (в граммах):\n"
        "<i>Например: 1000 (это 1 кг)</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AddProductForm.waiting_stock)
async def process_product_stock(message: Message, state: FSMContext):
    """Обработка количества товара и сохранение в БД"""
    try:
        stock_grams = int(message.text.strip())
        if stock_grams < 0:
            await message.answer("❌ Количество не может быть отрицательным. Введите еще раз:")
            return
    except ValueError:
        await message.answer("❌ Неверный формат. Введите число:")
        return

    # Получаем все данные из состояния
    data = await state.get_data()

    async for session in get_session():
        try:
            # Создаем новый товар
            product = Product(
                name=data['name'],
                description=data.get('description'),
                price=data['price'],
                category_id=data['category_id'],
                stock_grams=stock_grams,
                available=stock_grams > 0
            )

            session.add(product)
            await session.commit()

            await message.answer(
                f"✅ <b>Товар успешно добавлен!</b>\n\n"
                f"<b>Название:</b> {product.name}\n"
                f"<b>Цена:</b> {product.price} RSD/100г\n"
                f"<b>Количество:</b> {product.stock_grams}г\n"
                f"<b>ID:</b> {product.id}",
                parse_mode="HTML",
                reply_markup=back_to_admin_menu()
            )

        except Exception as e:
            await session.rollback()
            await message.answer(f"❌ Ошибка при сохранении товара: {e}")
        finally:
            await state.clear()


@router.callback_query(F.data == "admin:add_product")
async def add_product_from_menu(callback: CallbackQuery, state: FSMContext):
    """Добавление товара через меню админки"""
    if callback.from_user.id != settings.admin_id:
        return

    await start_add_product(callback.message, state)
    await callback.answer()