# app/handlers/admin/products.py - С ДОБАВЛЕНИЕМ ИЗОБРАЖЕНИЙ

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
    """Состояния для добавления товара с изображением"""
    waiting_name = State()
    waiting_description = State()
    waiting_price = State()
    waiting_category = State()
    waiting_image = State()  # ✅ НОВОЕ: состояние для изображения
    waiting_stock = State()


@router.message(Command("add_product"))
async def add_product_command(message: Message, state: FSMContext):
    """Команда /add_product - начало добавления товара"""
    # Проверка через middleware
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
    await state.set_state(AddProductForm.waiting_image)  # ✅ ПЕРЕХОД К ИЗОБРАЖЕНИЮ

    await message.answer(
        "🖼️ <b>Добавление изображения товара</b>\n\n"
        "Отправьте фото товара или введите:\n"
        "• <code>-</code> - пропустить добавление изображения\n"
        "• <code>ссылка</code> - URL изображения\n\n"
        "<i>Рекомендуется отправлять фото для лучшего вида в каталоге</i>",
        parse_mode="HTML"
    )


@router.message(AddProductForm.waiting_image)
async def process_product_image(message: Message, state: FSMContext, bot: Bot):
    """Обработка изображения товара"""
    image_url = None

    if message.photo:
        # Получаем самое большое изображение
        photo = message.photo[-1]

        # Используем file_id от Telegram
        file_info = await bot.get_file(photo.file_id)
        image_url = photo.file_id  # file_id можно использовать для отправки

        await message.answer("✅ Изображение получено и сохранено")

    elif message.text and message.text.strip() == "-":
        image_url = None
        await message.answer("✅ Пропускаем добавление изображения")

    elif message.text and message.text.strip().startswith(('http://', 'https://')):
        image_url = message.text.strip()
        await message.answer("✅ URL изображения сохранен")

    else:
        await message.answer(
            "❌ Пожалуйста, отправьте фото, URL или '-':\n\n"
            "• 📸 Фото товара\n"
            "• 🔗 Ссылка на изображение\n"
            "• ➖ '-' для пропуска",
            parse_mode="HTML"
        )
        return

    await state.update_data(image_url=image_url)
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
async def process_product_stock(message: Message, state: FSMContext, bot: Bot):
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
            # Получаем информацию о категории для названия
            category_result = await session.execute(
                select(Category).where(Category.id == data['category_id'])
            )
            category = category_result.scalar_one_or_none()

            # Создаем новый товар
            product = Product(
                name=data['name'],
                description=data.get('description'),
                price=data['price'],
                category_id=data['category_id'],
                stock_grams=stock_grams,
                available=stock_grams > 0,
                image_url=data.get('image_url')  # ✅ СОХРАНЯЕМ ИЗОБРАЖЕНИЕ
            )

            session.add(product)
            await session.commit()

            # Формируем сообщение об успехе
            success_text = f"✅ <b>Товар успешно добавлен!</b>\n\n"
            success_text += f"<b>Название:</b> {product.name}\n"
            success_text += f"<b>Категория:</b> {category.name if category else 'Неизвестно'}\n"
            success_text += f"<b>Цена:</b> {product.price} RSD/100г\n"
            success_text += f"<b>Количество:</b> {product.stock_grams}г\n"

            if product.image_url:
                success_text += f"<b>Изображение:</b> ✅ добавлено\n"
            else:
                success_text += f"<b>Изображение:</b> ❌ нет\n"

            success_text += f"<b>ID товара:</b> {product.id}"

            await message.answer(
                success_text,
                parse_mode="HTML",
                reply_markup=back_to_admin_menu()
            )

            # Если есть изображение (file_id), отправляем превью
            if product.image_url and not product.image_url.startswith(('http://', 'https://')):
                try:
                    await message.answer_photo(
                        photo=product.image_url,
                        caption=f"🖼️ Превью: {product.name}"
                    )
                except Exception as e:
                    print(f"Не удалось отправить превью изображения: {e}")

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

    await add_product_command(callback.message, state)
    await callback.answer()


# ✅ ДОБАВЛЯЕМ КОМАНДУ ДЛЯ ПРОСМОТРА ТОВАРОВ С ИЗОБРАЖЕНИЯМИ
@router.message(Command("view_products"))
async def view_products_with_images(message: Message):
    """Просмотр товаров с информацией об изображениях"""
    if str(message.from_user.id) != str(settings.admin_id):
        return

    async for session in get_session():
        result = await session.execute(
            select(Product).join(Category).order_by(Category.name, Product.name)
        )
        products = result.scalars().all()

        if not products:
            await message.answer("📭 Товаров пока нет")
            return

        text = "📋 <b>Список товаров:</b>\n\n"

        for product in products:
            emoji = "🖼️" if product.image_url else "📦"
            status = "✅" if product.available else "❌"
            text += f"{status} {emoji} <b>{product.name}</b>\n"
            text += f"   Категория: {product.category.name if product.category else 'Неизвестно'}\n"
            text += f"   Цена: {product.price} RSD/100г\n"
            text += f"   Остатки: {product.stock_grams}г\n"
            text += f"   ID: {product.id}\n\n"

        await message.answer(text, parse_mode="HTML")