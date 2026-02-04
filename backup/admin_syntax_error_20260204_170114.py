"""
Админка Barkery Shop (полная исправленная версия)
Версия с исправленной логикой уведомлений
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from database import get_session, Product, Category, CartItem, User
from config import settings
from keyboards import admin_main_keyboard, admin_categories_keyboard, admin_products_keyboard, admin_product_management_keyboard

logger = logging.getLogger(__name__)
admin_router = Router()

async def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id


async def check_and_notify_out_of_stock(bot, product_id, product_name, ordering_user_id=None):
    """Заглушка для функции уведомления о закончившемся товаре"""
    logger = logging.getLogger(__name__)
    logger.info(f"Товар закончился: {product_name} (ID: {product_id})")
    # В реальной реализации здесь была бы логика уведомления
    return 0  # Возвращаем 0 уведомленных пользователей

class AdminStates(StatesGroup):
    waiting_category_name = State()
    waiting_edit_category_name = State()
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_product_price = State()
    waiting_product_stock = State()
    waiting_product_unit_type = State()
    waiting_product_image = State()
    waiting_product_category = State()
    waiting_edit_field = State()
    waiting_edit_description = State()
    waiting_edit_confirm_name = State()
    waiting_edit_confirm_description = State()
    waiting_edit_confirm_price = State()
    waiting_edit_confirm_stock = State()
    waiting_edit_confirm_unit_type = State()
    waiting_edit_confirm_image = State()
    waiting_edit_confirm_category = State()
    waiting_edit_final_save = State()
    waiting_edit_value = State()


# Главная админ панель
@admin_router.message(Command("admin"))
async def admin_panel(message: Message):
    """Панель администратора"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    await message.answer(
            "👑 Панель администратора Barkery Shop\n\n\n"
            "Выберите действие:",
        reply_markup=admin_main_keyboard()
    )

# Управление категориями
@admin_router.callback_query(F.data == "admin_categories")
async def admin_categories(callback: CallbackQuery):
    """Управление категориями"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    async with get_session() as session:
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        if not categories:
            await callback.message.edit_text(
                "📦 Управление категориями\n\n"
                "Категорий нет. Добавьте первую категорию!",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_add_category")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
                ])
            )
            return
        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
        await callback.message.edit_text(
            "📦 Управление категориями\n\n"
            f"Всего категорий: {len(categories_list)}",
            reply_markup=admin_categories_keyboard(categories_list)
        )
    await callback.answer()

# Добавление категории
@admin_router.callback_query(F.data == "admin_add_category")
async def admin_add_category_handler(callback: CallbackQuery, state: FSMContext):
    """Добавление категории"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await state.set_state(AdminStates.waiting_category_name)
    await callback.message.edit_text(
        "➕ Добавление новой категории\n\n"
        "Введите название категории:"
    )
    await callback.answer()

@admin_router.message(AdminStates.waiting_category_name)
async def process_category_name(message: Message, state: FSMContext):
    """Обработка названия категории"""
    category_name = message.text.strip()
    if not category_name or len(category_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите снова:")
        return
    async with get_session() as session:
        # Проверяем существование категории
        stmt = select(Category).where(Category.name == category_name)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await message.answer("❌ Категория с таким названием уже существует. Введите другое:")
            return
        # Создаем категорию
        category = Category(name=category_name)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        await message.answer(f"✅ Категория '{category_name}' успешно создана! ID: {category.id}")
        await state.clear()
        # Возвращаем к списку категорий
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
        from keyboards import admin_categories_keyboard
        await message.answer(
            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
            reply_markup=admin_categories_keyboard(categories_list)
        )

# Редактирование категории
@admin_router.callback_query(F.data.startswith("admin_edit_category:"))
async def admin_edit_category_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование категории"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    category_id = int(callback.data.split(":")[1])
    await state.update_data(edit_category_id=category_id)
    await state.set_state(AdminStates.waiting_edit_category_name)
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if category:
            await callback.message.edit_text(
                f"✏️ Редактирование категории\n\n"
                f"Текущее название: {category.name}\n\n"
                "Введите новое название категории:"
            )
    await callback.answer()

@admin_router.message(AdminStates.waiting_edit_category_name)
async def process_edit_category_name(message: Message, state: FSMContext):
    """Обработка нового названия категории"""
    new_name = message.text.strip()
    if len(new_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите снова:")
        return
    data = await state.get_data()
    category_id = data.get("edit_category_id")
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if not category:
            await message.answer("❌ Категория не найдена")
            await state.clear()
            return
        # Проверяем нет ли другой категории с таким названием
        stmt = select(Category).where(Category.name == new_name, Category.id != category_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await message.answer("❌ Категория с таким названием уже существует. Введите другое:")
            return
        old_name = category.name
        category.name = new_name
        await session.commit()
        await message.answer(f"✅ Категория переименована: {old_name} → {new_name}")
        # Возвращаем к списку категорий
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
        from keyboards import admin_categories_keyboard
        await message.answer(
            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
            reply_markup=admin_categories_keyboard(categories_list)
        )
    await state.clear()

# Удаление категории
@admin_router.callback_query(F.data.startswith("admin_delete_category:"))
async def admin_delete_category_handler(callback: CallbackQuery):
    """Удаление категории"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    category_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        # Проверяем есть ли товары в категории
        stmt = select(Product).where(Product.category_id == category_id)
        result = await session.execute(stmt)
        products = result.scalars().all()
        if products:
            await callback.answer(
                f"❌ Нельзя удалить категорию с товарами. Сначала удалите {len(products)} товар(ов)",
                show_alert=True
            )
            return
        # Удаляем категорию
        await session.delete(category)
        await session.commit()
        await callback.answer(f"✅ Категория '{category.name}' удалена")
        # Обновляем список категорий
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
        await callback.message.edit_text(
            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
            reply_markup=admin_categories_keyboard(categories_list)
        )

# Управление товарами
@admin_router.callback_query(F.data == "admin_products")
async def admin_products(callback: CallbackQuery):
    """Управление товарами"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    async with get_session() as session:
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        if not categories:
            await callback.message.edit_text(
                "🛒 Управление товарами\n\n"
                "Сначала создайте категории.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📦 К категориям", callback_data="admin_categories")],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
                ])
            )
            return
        await callback.message.edit_text(
            "🛒 Управление товарами\n\n"
            f"Выберите категорию:",
            reply_markup=admin_products_keyboard(categories)
        )
    await callback.answer()

# Товары в выбранной категории
@admin_router.callback_query(F.data.startswith("admin_category_products:"))
async def admin_category_products_handler(callback: CallbackQuery):
    """Товары в выбранной категории"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    category_id = int(callback.data.split(":")[1])
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        stmt = select(Product).where(Product.category_id == category_id)
        result = await session.execute(stmt)
        products = result.scalars().all()
        products_list = [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock_grams": p.stock_grams,
                "available": p.available
            }
            for p in products
        ]
        await callback.message.edit_text(
            f"🛒 Товары категории: {category.name}\n\n"
            f"Количество товаров: {len(products_list)}",
            reply_markup=admin_product_management_keyboard(products_list, category_id)
        )
    await callback.answer()

# Добавление товара - исправленная версия
@admin_router.callback_query(F.data == "admin_add_product")
async def admin_add_product_handler(callback: CallbackQuery, state: FSMContext):
    """Добавление товара - исправленная версия"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    # Получаем список категорий
    async with get_session() as session:
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
    
    if not categories:
        await callback.answer("❌ Нет категорий. Сначала создайте категорию.", show_alert=True)
        return
    
    await state.update_data(available_categories=categories)
    await state.set_state(AdminStates.waiting_product_name)
    
    categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
    await callback.message.edit_text(
        "➕ Добавление нового товара\n\n"
        f"Доступные категории:\n{categories_text}\n\n"
        "Шаг 1 из 6: Введите название товара:"
    )
    await callback.answer()

@admin_router.message(AdminStates.waiting_product_name)
async def process_product_name_create(message: Message, state: FSMContext):
    """Обработка названия нового товара"""
    product_name = message.text.strip()
    if len(product_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите снова:")
        return
    
    await state.update_data(product_name=product_name)
    await state.set_state(AdminStates.waiting_product_description)
    await message.answer(
        f"✅ Название принято: {product_name}\n\n"
        "Шаг 2 из 6: Введите описание товара (или 'нет' если без описания):"
    )

@admin_router.message(AdminStates.waiting_product_description)
async def process_product_description_create(message: Message, state: FSMContext):
    """Обработка описания нового товара"""
    description = message.text.strip()
    if description.lower() == 'нет':
        description = ''
    
    await state.update_data(description=description)
    await state.set_state(AdminStates.waiting_product_price)
    await message.answer(
        f"✅ Описание принято\n\n"
        "Шаг 3 из 6: Введите цену в формате цена/шт или цена/гр:\n"
        "Пример для штучного товара: 750/шт\n"
        "Пример для весового товара: 500/гр"
    )

@admin_router.message(AdminStates.waiting_product_price)
async def process_product_price_create(message: Message, state: FSMContext):
    """Обработка цены нового товара с определением единиц измерения"""
    try:
        text = message.text.strip().lower()
        
        # Определяем единицы измерения
        if '/шт' in text:
            # Товар штучный
            price_text = text.replace('/шт', '').strip()
            unit_type = 'pieces'
            measurement_step = 1
            unit_text = 'штук'
            price_label = 'RSD/шт'
        elif '/гр' in text:
            # Товар весовой
            price_text = text.replace('/гр', '').strip()
            unit_type = 'grams'
            measurement_step = 100
            unit_text = 'грамм'
            price_label = 'RSD/100г'
        else:
            # По умолчанию - граммы (для обратной совместимости)
            price_text = text
            unit_type = 'grams'
            measurement_step = 100
            unit_text = 'грамм'
            price_label = 'RSD/100г'
        
        price = float(price_text)
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0. Введите снова:")
            return

        await state.update_data(
            price=price,
            unit_type=unit_type,
            measurement_step=measurement_step
        )
        
        # Пропускаем шаг выбора единиц измерения
        await state.set_state(AdminStates.waiting_product_stock)
        await message.answer(
            f"✅ Цена принята: {price} {price_label}\n"
            f"✅ Единицы измерения: {unit_text} (шаг: {measurement_step})\n\n"
            "Шаг 4 из 6: Введите количество (только число):\n"
            f"Для {unit_text}: {1000 if unit_type == 'grams' else 50} "
            f"(это {1000 if unit_type == 'grams' else 50} {unit_text})"
        )
    except ValueError:
        await message.answer(
            "❌ Введите число в формате: цена/шт или цена/гр\n\n"
            "Пример: 750/шт или 500/гр")

@admin_router.message(AdminStates.waiting_product_stock)
async def process_product_stock_create(message: Message, state: FSMContext):
    """Обработка количества для нового товара"""
    try:
        stock = int(message.text.strip())
        if stock < 0:
            await message.answer("❌ Количество не может быть отрицательным. Введите снова:")
            return

        await state.update_data(stock=stock)
        
        # Получаем данные из состояния для отображения правильных единиц
        data = await state.get_data()
        unit_type = data.get('unit_type', 'grams')
        measurement_step = data.get('measurement_step', 100)
        unit_text = 'грамм' if unit_type == 'grams' else 'штук'
        
        # Пропускаем шаг выбора единиц (они уже определены при вводе цены)
        await state.set_state(AdminStates.waiting_product_image)
        
        await message.answer(
            f"✅ Количество принято: {stock} {unit_text}\n"
            f"✅ Единицы измерения: {unit_text} (шаг: {measurement_step})\n\n"
            "Шаг 5 из 6: Загрузите изображение товара.\n"
            "Или отправьте 'пропустить' если без изображения:"
        )
    except ValueError:
        await message.answer("❌ Введите число. Введите снова:")

@admin_router.message(AdminStates.waiting_product_unit_type)
async def process_product_unit_type(message: Message, state: FSMContext):
    """Обработка единиц измерения товара"""
    unit_choice = message.text.strip()
    
    if unit_choice == '1':
        unit_type = 'grams'
        measurement_step = 100
        unit_text = 'грамм'
    elif unit_choice == '2':
        unit_type = 'pieces'
        measurement_step = 1
        unit_text = 'штук'
    else:
        await message.answer("❌ Введите '1' или '2':")
        return
    
    await state.update_data(unit_type=unit_type, measurement_step=measurement_step)
    await state.set_state(AdminStates.waiting_product_image)
    
    await message.answer(
        f"✅ Единицы измерения приняты: {unit_text} (шаг: {measurement_step})\n\n"
        "Шаг 6 из 6: Загрузите изображение товара.\n"
        "Или отправьте 'пропустить' если без изображения:"
    )

@admin_router.message(AdminStates.waiting_product_image)
async def process_product_image(message: Message, state: FSMContext):
    """Обработка изображения товара"""
    image_url = None

    if message.text and message.text.strip().lower() in ['пропустить', 'skip', 'без изображения']:
        await message.answer("✅ Пропускаем загрузку изображения")
    elif message.photo:
        # Используем file_id от телеграма
        image_url = message.photo[-1].file_id
        await message.answer(f"✅ Изображение получено")
    else:
        await message.answer("❌ Пожалуйста, загрузите изображение или отправьте 'пропустить'")
        return

    await state.update_data(image_url=image_url)

    # Получаем список категорий из состояния
    data = await state.get_data()
    categories = data.get('available_categories', [])

    if not categories:
        # Если категории утеряны, получаем их заново из БД
        from database import get_session, Category
        from sqlalchemy import select
        
        async with get_session() as session:
            stmt = select(Category).order_by(Category.name)
            result = await session.execute(stmt)
            categories = result.scalars().all()
            
            if categories:
                # Сохраняем в состоянии
                await state.update_data(available_categories=categories)
                categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
                
                await state.set_state(AdminStates.waiting_product_category)
                await message.answer(
                    f"✅ Изображение обработано\n\n"
                    f"Доступные категории:\n{categories_text}\n\n"
                    "Шаг 6 из 6: Введите ID категории для товара:"
                )
                return
            else:
                await message.answer("❌ В базе данных нет категорий. Сначала создайте категории.")
                await state.clear()
                return

    # Если категории есть, продолжаем как обычно
    categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
    await state.set_state(AdminStates.waiting_product_category)

    await message.answer(
        f"✅ Изображение обработано\n\n"
        f"Доступные категории:\n{categories_text}\n\n"
        "Шаг 6 из 6: Введите ID категории для товара:"
    )

@admin_router.message(AdminStates.waiting_product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обработка категории товара"""
    try:
        category_id = int(message.text.strip())
        
        # Получаем данные из состояния
        data = await state.get_data()
        categories = data.get('available_categories', [])
        
        # Проверяем существование категории
        category_exists = False
        for cat in categories:
            if cat.id == category_id:
                category_exists = True
                break
        
        if not category_exists:
            await message.answer(f"❌ Категория с ID {category_id} не найдена. Введите ID из списка:")
            return
        
        # Создаем товар
        async with get_session() as session:
            # Проверяем наличие всех необходимых данных
            required_fields = ['product_name', 'price', 'stock', 'unit_type', 'measurement_step', 'category_id']
            missing = []
            for field in required_fields:
                if field not in data:
                    missing.append(field)
            
            if missing:
                await message.answer(f"❌ Ошибка: отсутствуют данные: {missing}")
                await state.clear()
                return
            
            product = Product(
                name=data['product_name'],
                description=data.get('description', ''),
                price=data['price'],
                stock_grams=data['stock'],
                image_url=data.get('image_url'),
                unit_type=data.get('unit_type', 'grams'),
                measurement_step=data.get('measurement_step', 100),
                available=True,
                is_active=True,
                category_id=category_id
            )
            
            session.add(product)
            await session.commit()
            await session.refresh(product)
        
        await message.answer(
            f"✅ Товар успешно создан!\n\n"
            f"Название: {product.name}\n"
            f"Цена: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n"
            f"Количество: {product.stock_grams} ({'грамм' if product.unit_type == 'grams' else 'штук'})\n"
            f"Категория ID: {product.category_id}\n"
            f"Товар ID: {product.id}"
        )
        
        # Возвращаем к списку товаров
        await state.clear()
        from keyboards import admin_main_keyboard
        await message.answer(
            "👑 Панель администратора\n\nВыберите действие:",
            reply_markup=admin_main_keyboard()
        )
        
    except ValueError:
        await message.answer("❌ Введите число (ID категории):")
    except Exception as e:
        logger.error(f"Ошибка создания товара: {e}")
        logger.error(f"Данные в состоянии: {data}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        await message.answer(f"❌ Ошибка при создании товара: {str(e)}")
        await state.clear()

@admin_router.callback_query(F.data.startswith("admin_toggle_product:"))
async def admin_toggle_product_handler(callback: CallbackQuery):
    """Включение/выключение товара"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        product.available = not product.available
        await session.commit()
        status = "включен" if product.available else "выключен"
        await callback.answer(f"✅ Товар '{product.name}' {status}")
        # Обновляем список товаров
        category = await session.get(Category, category_id)
        stmt = select(Product).where(Product.category_id == category_id)
        result = await session.execute(stmt)
        products = result.scalars().all()
        products_list = [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock_grams": p.stock_grams,
                "available": p.available
            }
            for p in products
        ]
        await callback.message.edit_text(
            f"🛒 Товары категории: {category.name}\n\n"
            f"Количество товаров: {len(products_list)}",
            reply_markup=admin_product_management_keyboard(products_list, category_id)
        )

# Обновление остатков товара
@admin_router.callback_query(F.data.startswith("admin_update_stock:"))
async def admin_update_stock_handler(callback: CallbackQuery, state: FSMContext):
    """Обновление остатков товара с проверкой корзин пользователей"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    
    await state.update_data(
        product_id=product_id,
        category_id=category_id
    )
    await state.set_state(AdminStates.waiting_edit_field)
    
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if product:
            # Проверяем есть ли этот товар в корзинах пользователей
            stmt = select(func.sum(CartItem.quantity)).where(
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            in_carts = result.scalar() or 0
            
            await state.update_data(edit_field='stock_grams')
            
            if in_carts > 0:
                warning = f"⚠️ Внимание: этот товар есть в корзинах у пользователей ({in_carts}{'г' if product.unit_type == 'grams' else 'шт'})\n"
            else:
                warning = ""
            
            await callback.message.edit_text(
                f"📦 Обновление остатков\n\n"
                f"Товар: {product.name}\n"
                f"Текущие остатки: {product.stock_grams}{'г' if product.unit_type == 'grams' else 'шт'}\n"
                f"{warning}\n"
                "Введите новое количество:"
            )
        else:
            await callback.message.edit_text(
                "📦 Обновление остатков\n\n"
                "Введите новое количество:"
            )
    await callback.answer()

# Редактирование названия товара
@admin_router.callback_query(F.data.startswith("admin_edit_product_name:"))
async def admin_edit_product_name_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование названия товара"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    await state.update_data(
        product_id=product_id,
        category_id=category_id,
        edit_field='name'
    )
    await state.set_state(AdminStates.waiting_edit_field)
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if product:
            await callback.message.edit_text(
                f"✏️ Редактирование названия\n\n"
                f"Товар: {product.name}\n"
                f"Текущее название: {product.name}\n\n"
                "Введите новое название товара:"
            )
        else:
            await callback.message.edit_text(
                f"✏️ Редактирование названия\n\n"
                "Введите новое название товара:"
            )
    await callback.answer()

# Редактирование цены товара
@admin_router.callback_query(F.data.startswith("admin_edit_product_price:"))
async def admin_edit_product_price_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование цены товара"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    await state.update_data(
        product_id=product_id,
        category_id=category_id,
        edit_field='price'
    )
    await state.set_state(AdminStates.waiting_edit_field)
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if product:
            await callback.message.edit_text(
                f"💰 Редактирование цены\n\n"
                f"Товар: {product.name}\n"
                f"Текущая цена: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n\n"
                "Введите новую цены:"
            )
        else:
            await callback.message.edit_text(
                f"💰 Редактирование цены\n\n"
                "Введите новую цены:"
            )
    await callback.answer()

# Редактирование единиц измерения товара

# Редактирование описания товара
@admin_router.callback_query(F.data.startswith("admin_edit_product_description:"))
async def admin_edit_product_description_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания товара"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    await state.update_data(
        product_id=product_id,
        category_id=category_id,
        edit_field='description'
    )
    await state.set_state(AdminStates.waiting_edit_field)
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if product:
            current_desc = product.description or "нет описания"
            await callback.message.edit_text(
                f"📝 Редактирование описания\n\n"
                f"Товар: {product.name}\n"
                f"Текущее описание: {current_desc}\n\n"
                "Введите новое описание товара (или 'нет' для удаления):"
            )
        else:
            await callback.message.edit_text(
                f"📝 Редактирование описания\n\n"
                "Введите новое описание товара (или 'нет' для удаления):"
            )
    await callback.answer()
@admin_router.callback_query(F.data.startswith("admin_edit_product_units:"))
async def admin_edit_product_units_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование единиц измерения товара - исправленная версия"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    
    # Устанавливаем состояние для редактирования единиц
    await state.update_data(
        product_id=product_id,
        category_id=category_id,
        edit_field='unit_type'
    )
    
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if product:
            current_unit = "грамм" if product.unit_type == 'grams' else "штук"
            await callback.message.edit_text(
                f"📏 Редактирование единиц измерения\n\n"
                f"Товар: {product.name}\n"
                f"Текущие единицы: {current_unit} (шаг: {product.measurement_step})\n\n"
                "Выберите новые единицы измерения товара:\n"
                "1. Граммы (измеряется в граммах, шаг 100г)\n"
                "2. Штуки (измеряется в штуках, шаг 1шт)\n\n"
                "Введите '1' или '2':"
            )
        else:
            await callback.message.edit_text(
                f"📏 Редактирование единиц измерения\n\n"
                "Выберите единицы измерения товара:\n"
                "1. Граммы (измеряется в граммах, шаг 100г)\n"
                "2. Штуки (измеряется в штуках, шаг 1шт)\n\n"
                "Введите '1' или '2':"
            )
    
    await state.set_state(AdminStates.waiting_edit_field)
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_edit_product_full:"))
async def admin_edit_product_full_handler(callback: CallbackQuery, state: FSMContext):
    """Правильное пошаговое редактирование товара с вопросами 'хотите изменить?'"""
    logger = logging.getLogger(__name__)
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])

    await state.update_data(
        edit_product_id=product_id,
        edit_category_id=category_id,
        edit_step=0,
        edit_changes={}
    )

    # Показываем первый шаг
    await show_proper_edit_step(callback, state)
    await callback.answer()

async def show_proper_edit_step(callback_or_message, state: FSMContext):
    """Показать текущий шаг редактирования с вопросом 'хотите изменить?'"""
    from aiogram.types import CallbackQuery, Message
    
    data = await state.get_data()
    step = data.get('edit_step', 0)
    product_id = data.get('edit_product_id')
    
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            if isinstance(callback_or_message, CallbackQuery):
                await callback_or_message.answer("❌ Товар не найден", show_alert=True)
            else:
                await callback_or_message.answer("❌ Товар не найден")
            await state.clear()
            return
        
        # Получаем название категории
        category_name = "неизвестно"
        if product.category_id:
            category = await session.get(Category, product.category_id)
            if category:
                category_name = category.name
        
        # Шаги редактирования
        steps = [
            {
                "name": "название",
                "value": product.name,
                "field": "name",
                "state": AdminStates.waiting_edit_confirm_name,
                "prompt": "✏️ Введите новое название товара:"
            },
            {
                "name": "описание", 
                "value": product.description or "нет описания",
                "field": "description",
                "state": AdminStates.waiting_edit_confirm_description,
                "prompt": "📝 Введите новое описание товара (или 'нет' для удаления):"
            },
            {
                "name": "цена",
                "value": f"{product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}",
                "field": "price",
                "state": AdminStates.waiting_edit_confirm_price,
                "prompt": "💰 Введите новую цену в формате цена/шт или цена/гр:\\nПример: 750/шт или 500/гр"
            },
            {
                "name": "остатки",
                "value": f"{product.stock_grams}{'г' if product.unit_type == 'grams' else 'шт'}",
                "field": "stock_grams",
                "state": AdminStates.waiting_edit_confirm_stock,
                "prompt": f"📦 Введите новое количество ({'в граммах' if product.unit_type == 'grams' else 'в штуках'}):"
            },
            {
                "name": "единицы измерения",
                "value": f"{'грамм' if product.unit_type == 'grams' else 'штук'} (шаг: {product.measurement_step})",
                "field": "unit_type",
                "state": AdminStates.waiting_edit_confirm_unit_type,
                "prompt": "📏 Выберите единицы измерения:\\n1. Граммы (измеряется в граммах, шаг 100г)\\n2. Штуки (измеряется в штуках, шаг 1шт)\\nВведите '1' или '2':"
            },
            {
                "name": "изображение",
                "value": "есть" if product.image_url else "нет",
                "field": "image_url",
                "state": AdminStates.waiting_edit_confirm_image,
                "prompt": "🖼️ Загрузите новое изображение товара или отправьте 'пропустить':"
            },
            {
                "name": "категория",
                "value": category_name,
                "field": "category_id",
                "state": AdminStates.waiting_edit_confirm_category,
                "prompt": "📂 Введите ID новой категории (список категорий будет показан отдельно):"
            }
        ]
        
        if step >= len(steps):
            # Все шаги пройдены, сохраняем изменения
            await save_proper_changes(callback_or_message, state)
            return
        
        current_step = steps[step]
        
        message_text = (
            f"✏️ Пошаговое редактирование товара

"
            f"Товар: {product.name}
"
            f"Шаг {step + 1} из {len(steps)}: {current_step['name']}
"
            f"Текущее значение: {current_step['value']}

"
            f"Хотите изменить {current_step['name']}? (да/нет):"
        )
        
        # Устанавливаем состояние для этого шага
        await state.set_state(current_step['state'])
        await state.update_data(
            current_field=current_step['field'],
            current_prompt=current_step['prompt']
        )
        
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(message_text)
        else:
            await callback_or_message.answer(message_text)

# Обработчики для каждого шага (все используют одну логику)
async def handle_edit_confirmation(message: Message, state: FSMContext, next_state):
    """Обработка ответа 'да/нет' на вопрос об изменении"""
    response = message.text.strip().lower()
    data = await state.get_data()
    
    if response in ['да', 'д', 'yes', 'y', '+']:
        # Пользователь хочет изменить
        current_prompt = data.get('current_prompt', 'Введите новое значение:')
        await state.set_state(AdminStates.waiting_edit_field)
        await message.answer(current_prompt)
    elif response in ['нет', 'н', 'no', 'n', '-']:
        # Пользователь не хочет менять, переходим к следующему шагу
        await state.update_data(edit_step=data.get('edit_step', 0) + 1)
        await show_proper_edit_step(message, state)
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет':")

# Создаем обработчики для каждого состояния
@admin_router.message(AdminStates.waiting_edit_confirm_name)
async def process_proper_edit_name(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_confirm_description)

@admin_router.message(AdminStates.waiting_edit_confirm_description)
async def process_proper_edit_description(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_confirm_price)

@admin_router.message(AdminStates.waiting_edit_confirm_price)
async def process_proper_edit_price(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_confirm_stock)

@admin_router.message(AdminStates.waiting_edit_confirm_stock)
async def process_proper_edit_stock(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_confirm_unit_type)

@admin_router.message(AdminStates.waiting_edit_confirm_unit_type)
async def process_proper_edit_unit_type(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_confirm_image)

@admin_router.message(AdminStates.waiting_edit_confirm_image)
async def process_proper_edit_image(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_confirm_category)

@admin_router.message(AdminStates.waiting_edit_confirm_category)
async def process_proper_edit_category(message: Message, state: FSMContext):
    await handle_edit_confirmation(message, state, AdminStates.waiting_edit_final_save)

# Обработчик ввода нового значения
@admin_router.message(AdminStates.waiting_edit_field)
async def process_proper_edit_field(message: Message, state: FSMContext):
    """Обработка ввода нового значения для поля"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 [DEBUG] process_proper_edit_field вызван")
    
    data = await state.get_data()
    field = data.get('current_field')
    product_id = data.get('edit_product_id')

    if not field or not product_id:
        logger.error(f"❌ Нет field или product_id в данных: {data}")
        await message.answer("❌ Ошибка данных. Попробуйте снова.")
        await state.clear()
        return

    value = message.text.strip()
    logger.info(f"🔍 [DEBUG] Обрабатываем поле '{field}' со значением: '{value}'")
    
    # Сохраняем изменение
    changes = data.get('edit_changes', {})
    
    # Специальная обработка для некоторых полей
    if field == 'description':
        if value.lower() == 'нет':
            value = ''
        changes[field] = value
        logger.info(f"🔍 [DEBUG] Сохранено описание: '{value}'")
    elif field == 'price':
        # Обработка цены с единицами измерения
        try:
            if '/шт' in value.lower():
                price_text = value.lower().replace('/шт', '').strip()
                changes['price'] = float(price_text)
                changes['unit_type'] = 'pieces'
                changes['measurement_step'] = 1
                logger.info(f"🔍 [DEBUG] Цена за штуку: {changes['price']}")
            elif '/гр' in value.lower():
                price_text = value.lower().replace('/гр', '').strip()
                changes['price'] = float(price_text)
                changes['unit_type'] = 'grams'
                changes['measurement_step'] = 100
                logger.info(f"🔍 [DEBUG] Цена за 100г: {changes['price']}")
            else:
                # По умолчанию граммы
                changes['price'] = float(value)
                changes['unit_type'] = 'grams'
                changes['measurement_step'] = 100
                logger.info(f"🔍 [DEBUG] Цена (по умолчанию граммы): {changes['price']}")
        except ValueError:
            await message.answer("❌ Неверный формат цены. Пример: 750/шт или 500/гр")
            return
    elif field == 'unit_type':
        if value == '1':
            changes['unit_type'] = 'grams'
            changes['measurement_step'] = 100
            logger.info(f"🔍 [DEBUG] Установлены граммы")
        elif value == '2':
            changes['unit_type'] = 'pieces'
            changes['measurement_step'] = 1
            logger.info(f"🔍 [DEBUG] Установлены штуки")
        else:
            await message.answer("❌ Введите '1' или '2':")
            return
    elif field == 'stock_grams':
        try:
            changes['stock_grams'] = int(value)
            if changes['stock_grams'] < 0:
                await message.answer("❌ Количество не может быть отрицательным")
                return
            logger.info(f"🔍 [DEBUG] Установлено количество: {changes['stock_grams']}")
        except ValueError:
            await message.answer("❌ Введите целое число")
            return
    elif field == 'category_id':
        try:
            changes['category_id'] = int(value)
            logger.info(f"🔍 [DEBUG] Установлена категория ID: {changes['category_id']}")
        except ValueError:
            await message.answer("❌ Введите числовой ID категории")
            return
    elif field == 'image_url':
        if value.lower() in ['пропустить', 'skip', 'без изображения']:
            changes['image_url'] = None
            logger.info(f"🔍 [DEBUG] Изображение пропущено")
        elif message.photo:
            # Используем file_id от телеграма
            changes['image_url'] = message.photo[-1].file_id
            logger.info(f"🔍 [DEBUG] Сохранено изображение (file_id)")
        else:
            # Сохраняем как URL или текст
            changes['image_url'] = value
            logger.info(f"🔍 [DEBUG] Сохранен URL изображения: {value}")
    else:
        # Для обычных полей (name и других)
        changes[field] = value
        logger.info(f"🔍 [DEBUG] Сохранено поле {field}: {value}")
    
    # Обновляем состояние
    current_step = data.get('edit_step', 0)
    new_step = current_step + 1
    logger.info(f"🔍 [DEBUG] Обновляем шаг: {current_step} -> {new_step}")
    
    await state.update_data(edit_changes=changes, edit_step=new_step)
    await show_proper_edit_step(message, state)

@admin_router.message(AdminStates.waiting_edit_final_save)
async def process_proper_edit_final(message: Message, state: FSMContext):
    """Обработка последнего шага редактирования"""
    response = message.text.strip().lower()
    
    if response in ['да', 'д', 'yes', 'y', '+']:
        # Пользователь хочет изменить категорию
        await state.set_state(AdminStates.waiting_edit_field)
        await state.update_data(current_field='category_id')
        await message.answer("📂 Введите ID новой категории:")
    elif response in ['нет', 'н', 'no', 'n', '-']:
        # Пользователь не хочет менять категорию, сохраняем все изменения
        data = await state.get_data()
        await save_proper_changes(message, state)
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет':")
    
    value = message.text.strip()
    
    # Сохраняем изменение
    changes = data.get('edit_changes', {})
    
    # Специальная обработка для некоторых полей
    if field == 'description':
        if value.lower() == 'нет':
            value = ''
        changes[field] = value
    elif field == 'price':
        # Обработка цены с единицами измерения
        try:
            if '/шт' in value.lower():
                price_text = value.lower().replace('/шт', '').strip()
                changes['price'] = float(price_text)
                changes['unit_type'] = 'pieces'
                changes['measurement_step'] = 1
            elif '/гр' in value.lower():
                price_text = value.lower().replace('/гр', '').strip()
                changes['price'] = float(price_text)
                changes['unit_type'] = 'grams'
                changes['measurement_step'] = 100
            else:
                # По умолчанию граммы
                changes['price'] = float(value)
                changes['unit_type'] = 'grams'
                changes['measurement_step'] = 100
        except ValueError:
            await message.answer("❌ Неверный формат цены. Пример: 750/шт или 500/гр")
            return
    elif field == 'unit_type':
        if value == '1':
            changes['unit_type'] = 'grams'
            changes['measurement_step'] = 100
        elif value == '2':
            changes['unit_type'] = 'pieces'
            changes['measurement_step'] = 1
        else:
            await message.answer("❌ Введите '1' или '2':")
            return
    elif field == 'stock_grams':
        try:
            changes['stock_grams'] = int(value)
            if changes['stock_grams'] < 0:
                await message.answer("❌ Количество не может быть отрицательным")
                return
        except ValueError:
            await message.answer("❌ Введите целое число")
            return
    elif field == 'category_id':
        try:
            changes['category_id'] = int(value)
        except ValueError:
            await message.answer("❌ Введите числовой ID категории")
            return
    elif field == 'image_url':
        if value.lower() in ['пропустить', 'skip', 'без изображения']:
            changes['image_url'] = None
        elif message.photo:
            # Используем file_id от телеграма
            changes['image_url'] = message.photo[-1].file_id
        else:
            # Сохраняем как URL или текст
            changes['image_url'] = value
    else:
        # Для обычных полей (name)
        changes[field] = value
    
    await state.update_data(edit_changes=changes, edit_step=data.get('edit_step', 0) + 1)
    await show_proper_edit_step(message, state)

async def save_proper_changes(callback_or_message, state: FSMContext):
    """Сохранение всех изменений товара"""
    from aiogram.types import CallbackQuery, Message
    
    data = await state.get_data()
    product_id = data.get('edit_product_id')
    category_id = data.get('edit_category_id')
    changes = data.get('edit_changes', {})
    
    if not changes:
        message_text = "⚠️ Ничего не изменено. Редактирование отменено."
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(message_text)
        else:
            await callback_or_message.answer(message_text)
        await state.clear()
        return
    
    try:
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                message_text = "❌ Товар не найден"
                if isinstance(callback_or_message, CallbackQuery):
                    await callback_or_message.message.edit_text(message_text)
                else:
                    await callback_or_message.answer(message_text)
                await state.clear()
                return
            
            # Применяем изменения
            for field, value in changes.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            await session.commit()
            
            # Показываем результат
            changes_list = "\n".join([f"• {k}: {v}" for k, v in changes.items()])
            message_text = f"✅ Товар успешно обновлен!\n\nИзменения:\n{changes_list}"
            
            if isinstance(callback_or_message, CallbackQuery):
                await callback_or_message.message.edit_text(message_text)
            else:
                await callback_or_message.answer(message_text)
            
            # Возвращаем к списку товаров
            await show_proper_products_after_edit(callback_or_message, category_id)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка сохранения товара: {e}")
        message_text = f"❌ Ошибка сохранения: {e}"
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(message_text)
        else:
            await callback_or_message.answer(message_text)
    
    await state.clear()

async def show_proper_products_after_edit(callback_or_message, category_id: int):
    """Показать список товаров после редактирования"""
    from aiogram.types import CallbackQuery, Message
    
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if not category:
            message_text = "❌ Категория не найдена"
            if isinstance(callback_or_message, CallbackQuery):
                await callback_or_message.message.edit_text(message_text)
            else:
                await callback_or_message.answer(message_text)
            return
        
        stmt = select(Product).where(Product.category_id == category_id)
        result = await session.execute(stmt)
        products = result.scalars().all()
        
        products_list = [
            {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "stock_grams": p.stock_grams,
                "available": p.available,
                "unit_type": p.unit_type
            }
            for p in products
        ]
        
        from keyboards import admin_product_management_keyboard
        message_text = f"🛒 Товары категории: {category.name}\n\nКоличество товаров: {len(products_list)}"
        
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(
                message_text,
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )
        else:
            await callback_or_message.answer(
                message_text,
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )

# Правильная функция admin_back
@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Назад в главное меню админки"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    from keyboards import admin_main_keyboard
    await callback.message.edit_text(
        "👑 Панель администратора Barkery Shop\\n\\n\\nВыберите действие:",
        reply_markup=admin_main_keyboard()
    )
    await callback.answer()
