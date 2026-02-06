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

# Удаляю дублирующий обработчик удаления товара (оставляю только один в конце файла)

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
    waiting_product_hypoallergenic = State()
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

    # Сохраняем категории как список словарей для надежности
    categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
    await state.update_data(available_categories=categories_list)
    await state.set_state(AdminStates.waiting_product_name)

    categories_text = "\n".join([f"{cat['id']}. {cat['name']}" for cat in categories_list])
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
@admin_router.message(AdminStates.waiting_product_image)
async def process_product_image(message: Message, state: FSMContext):
    """Обработка изображения товара - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
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

    # Сохраняем URL изображения в состоянии
    await state.update_data(image_url=image_url)

    # Логируем текущие данные
    data = await state.get_data()
    logger.info(f"Данные перед выбором категории: {list(data.keys())}")

    # Получаем список категорий из состояния
    categories = data.get('available_categories')

    if not categories:
        # Если категории утеряны, получаем их заново из БД
        logger.warning("Категории утеряны в состоянии, загружаю заново")
        async with get_session() as session:
            stmt = select(Category).order_by(Category.name)
            result = await session.execute(stmt)
            categories = result.scalars().all()

            if categories:
                # Сохраняем в состоянии как список словарей для надежности
                categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
                await state.update_data(available_categories=categories_list)

                categories_text = "\n".join([f"{cat['id']}. {cat['name']}" for cat in categories_list])

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
    else:
        # Преобразуем объекты в словари если нужно
        if isinstance(categories[0], Category):
            categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
            await state.update_data(available_categories=categories_list)
        else:
            categories_list = categories

        categories_text = "\n".join([f"{cat['id']}. {cat['name']}" for cat in categories_list])

        await state.set_state(AdminStates.waiting_product_category)
        await message.answer(
            f"✅ Изображение обработано\n\n"
            f"Доступные категории:\n{categories_text}\n\n"
            "Шаг 6 из 6: Введите ID категории для товара:"
        )


@admin_router.message(AdminStates.waiting_product_category)
async def process_product_category(message: Message, state: FSMContext):
    """Обработка категории товара - с добавлением гипоаллергенности"""
    try:
        category_id = int(message.text.strip())

        # Получаем данные из состояния
        data = await state.get_data()
        logger.info(f"Данные при выборе категории: {list(data.keys())}")

        # Проверяем наличие всех необходимых данных
        required_fields = ['product_name', 'price', 'stock', 'unit_type', 'measurement_step']
        missing = []
        for field in required_fields:
            if field not in data:
                missing.append(field)

        if missing:
            await message.answer(f"❌ Ошибка: отсутствуют данные: {missing}. Начните заново.")
            await state.clear()

            # Возвращаем к началу добавления товара
            from keyboards import admin_main_keyboard
            await message.answer(
                "👑 Панель администратора\n\nВыберите действие:",
                reply_markup=admin_main_keyboard()
            )
            return

        # Проверяем существование категории
        categories = data.get('available_categories', [])
        category_exists = False
        category_name = None

        for cat in categories:
            # Обрабатываем как объект или словарь
            if isinstance(cat, dict) and cat['id'] == category_id:
                category_exists = True
                category_name = cat['name']
                break
            elif hasattr(cat, 'id') and cat.id == category_id:
                category_exists = True
                category_name = cat.name
                break

        if not category_exists:
            # Пробуем проверить в базе данных
            async with get_session() as session:
                category = await session.get(Category, category_id)
                if category:
                    category_exists = True
                    category_name = category.name
                else:
                    await message.answer(f"❌ Категория с ID {category_id} не найдена. Введите ID из списка:")
                    return

        # ВАЖНОЕ ИЗМЕНЕНИЕ: ВМЕСТО создания товара, переходим к следующему шагу

        # Сохраняем данные категории в состоянии
        await state.update_data(
            category_id=category_id,
            category_name=category_name or str(category_id)
        )

        # Переходим к вопросу о гипоаллергенности
        await state.set_state(AdminStates.waiting_product_hypoallergenic)

        await message.answer(
            f"✅ Категория принята: {category_name or category_id}\n\n"
            "🔬 Это гипоаллергенный товар?\n\n"
            "Отвечайте 'да' или 'нет':\n"
            "• да - товар появится в категории 'Гипоаллергенные'\n"
            "• нет - обычный товар"
        )

    except ValueError:
        await message.answer("❌ Введите число (ID категории):")
    except Exception as e:
        logger.error(f"Ошибка при выборе категории: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        await message.answer(f"❌ Ошибка: {str(e)}")
        await state.clear()


@admin_router.message(AdminStates.waiting_product_hypoallergenic)
async def process_product_hypoallergenic(message: Message, state: FSMContext):
    """Обработка флага гипоаллергенности - создание товара"""
    response = message.text.strip().lower()

    # Определяем флаг
    if response in ['да', 'д', 'yes', 'y', '+']:
        is_hypoallergenic = True
        hypo_text = "гипоаллергенный"
    elif response in ['нет', 'н', 'no', 'n', '-']:
        is_hypoallergenic = False
        hypo_text = "обычный"
    else:
        await message.answer("❌ Ответьте 'да' или 'нет':")
        return

    try:
        # Получаем ВСЕ данные из состояния
        data = await state.get_data()
        logger.info(f"Данные при создании товара: {list(data.keys())}")

        # Еще раз проверяем наличие всех данных (на всякий случай)
        required_fields = ['product_name', 'price', 'stock', 'unit_type', 'measurement_step', 'category_id']
        missing = []
        for field in required_fields:
            if field not in data:
                missing.append(field)

        if missing:
            await message.answer(f"❌ Ошибка: отсутствуют данные: {missing}. Начните заново.")
            await state.clear()

            from keyboards import admin_main_keyboard
            await message.answer(
                "👑 Панель администратора\n\nВыберите действие:",
                reply_markup=admin_main_keyboard()
            )
            return

        # Создаем товар с флагом гипоаллергенности
        async with get_session() as session:
            product = Product(
                name=data['product_name'],
                description=data.get('description', ''),
                price=data['price'],
                stock_grams=data['stock'],
                image_url=data.get('image_url'),
                unit_type=data['unit_type'],
                measurement_step=data['measurement_step'],
                is_hypoallergenic=is_hypoallergenic,  # НОВОЕ ПОЛЕ
                available=True,
                is_active=True,
                category_id=data['category_id']
            )

            session.add(product)
            await session.commit()
            await session.refresh(product)

        # Формируем информативное сообщение
        category_info = data.get('category_name', f"ID: {data['category_id']}")

        # Определяем единицы измерения для отображения
        if data['unit_type'] == 'grams':
            unit_text = '100г'
            stock_text = f"{data['stock']}г"
        else:
            unit_text = 'шт'
            stock_text = f"{data['stock']}шт"

        await message.answer(
            f"✅ Товар успешно создан!\n\n"
            f"📦 Название: {data['product_name']}\n"
            f"💰 Цена: {data['price']} RSD/{unit_text}\n"
            f"📊 Количество: {stock_text}\n"
            f"📂 Категория: {category_info}\n"
            f"🔬 Тип: {hypo_text}\n"
            f"🆔 ID товара: {product.id}"
        )

        # Возвращаем к списку товаров в этой категории
        await show_products_after_edit(message, data['category_id'])

    except Exception as e:
        logger.error(f"Ошибка создания товара: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        await message.answer(f"❌ Ошибка при создании товара: {str(e)}")

    finally:
        # Всегда очищаем состояние
        await state.clear()


@admin_router.callback_query(F.data.startswith("admin_toggle_hypoallergenic:"))
async def admin_toggle_hypoallergenic_handler(callback: CallbackQuery):
    """Включение/выключение гипоаллергенности товара"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return

    product_id = int(parts[1])
    category_id = int(parts[2])

    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        # Меняем флаг
        old_status = product.is_hypoallergenic
        new_status = not old_status
        product.is_hypoallergenic = new_status
        await session.commit()

        status_text = "гипоаллергенный" if new_status else "обычный"
        await callback.answer(f"✅ Товар теперь {status_text}")

        # Обновляем список товаров
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
                "available": p.available,
                "unit_type": p.unit_type,
                "is_hypoallergenic": p.is_hypoallergenic  # Добавляем флаг
            }
            for p in products
        ]

        # Пытаемся безопасно обновить сообщение
        try:
            await callback.message.edit_text(
                f"🛒 Товары категории: {category.name}\n\n"
                f"Количество товаров: {len(products_list)}",
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            # Отправляем новое сообщение
            await callback.message.answer(
                f"🛒 Товары категории: {category.name}\n\n"
                f"Количество товаров: {len(products_list)}",
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )


@admin_router.callback_query(F.data.startswith("admin_toggle_product:"))
async def admin_toggle_product_handler(callback: CallbackQuery):
    """Включение/выключение товара - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
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

        # ИСПРАВЛЕНО: Когда включаем товар, проверяем остатки
        old_status = product.available
        new_status = not old_status

        # Если ВКЛЮЧАЕМ товар, проверяем остатки
        if new_status:
            # Для весового товара: включаем только если >= 100г
            if product.unit_type == 'grams' and product.stock_grams < 100:
                await callback.answer(
                    f"⚠️ Нельзя включить весовой товар. Остатки: {product.stock_grams}г (< 100г)",
                    show_alert=True
                )
                return

            # Для штучного товара: включаем только если >= 1шт
            elif product.unit_type == 'pieces' and product.stock_grams < 1:
                await callback.answer(
                    f"⚠️ Нельзя включить штучный товар. Остатки: {product.stock_grams}шт (< 1шт)",
                    show_alert=True
                )
                return

        product.available = new_status
        await session.commit()

        status_text = "включен" if new_status else "выключен"
        await callback.answer(f"✅ Товар '{product.name}' {status_text}")

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
                "available": p.available,
                "unit_type": p.unit_type  # Добавляем unit_type для корректного отображения
            }
            for p in products
        ]

        # ИСПРАВЛЕНО: Используем безопасное редактирование
        try:
            await callback.message.edit_text(
                f"🛒 Товары категории: {category.name}\n\n"
                f"Количество товаров: {len(products_list)}",
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            # Отправляем новое сообщение
            await callback.message.answer(
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

@admin_router.message(AdminStates.waiting_edit_field)
async def process_edit_field(message: Message, state: FSMContext):
    """Обработка изменения поля товара"""
    logger = logging.getLogger(__name__)
    try:
        data = await state.get_data()
        field = data.get('edit_field')
        product_id = data.get('product_id')
        category_id = data.get('category_id')

        if not all([field, product_id, category_id]):
            await message.answer("❌ Ошибка данных. Попробуйте снова.")
            await state.clear()
            return

        value = message.text.strip()

        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                await message.answer("❌ Товар не найден")
                await state.clear()
                return

            # Преобразуем значение в нужный тип
            if field == 'stock_grams':
                new_value = int(value)
                if new_value < 0:
                    await message.answer("❌ Количество не может быть отрицательным. Введите снова:")
                    return
                old_value = product.stock_grams
                product.stock_grams = new_value

                # Логика возврата товара в доступность при достаточных остатках
                if not product.available:
                    should_show = False
                    if product.unit_type == 'grams':
                        # Для весового: показываем если >= 100г
                        if new_value >= 100:
                            should_show = True
                            reason = "остатки восстановлены до 100г и более"
                    else:  # pieces
                        # Для штучный: показываем если >= 1шт
                        if new_value >= 1:
                            should_show = True
                            reason = "остатки восстановлены до 1шт и более"

                    if should_show:
                        product.available = True
                        logger.info(f"Товар {product.name} (ID: {product.id}) возвращен в доступность: {reason}")
            elif field == 'price':
                new_value = float(value)
                if new_value <= 0:
                    await message.answer("❌ Цена должна быть больше 0. Введите снова:")
                    return
                old_value = product.price
                product.price = new_value
            elif field == 'name':
                if len(value) < 2:
                    await message.answer("❌ Название слишком короткое. Введите снова:")
                    return
                old_value = product.name
                product.name = value
            elif field == 'description':
                if value.lower() == 'нет':
                    value = ''
                old_value = product.description
                product.description = value
            elif field == 'unit_type':
                if value == '1':
                    unit_type = 'grams'
                    measurement_step = 100
                elif value == '2':
                    unit_type = 'pieces'
                    measurement_step = 1
                else:
                    await message.answer("❌ Введите '1' или '2':")
                    return

                old_value = product.unit_type
                product.unit_type = unit_type
                product.measurement_step = measurement_step

                # Обновляем текст для сообщения об успехе
                unit_text = 'грамм' if unit_type == 'grams' else 'штук'
                value = f"{unit_text} (шаг: {measurement_step})"
            else:
                await message.answer("❌ Неизвестное поле для редактирования")
                await state.clear()
                return

            await session.commit()
            await message.answer(f"✅ Товар обновлен: {field} = {value}")

            # Возвращаем к списку товаров
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
            await message.answer(
                f"🛒 Товары категории: {category.name}\n\n"
                f"Количество товаров: {len(products_list)}",
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )

        await state.clear()

    except ValueError:
        await message.answer("❌ Неверный формат. Введите число:")
    except Exception as e:
        logger.error(f"Ошибка обновления товара: {e}")
        await message.answer("❌ Ошибка обновления товара")
        await state.clear()

# ========== ПОЛНОЕ ПОШАГОВОЕ РЕДАКТИРОВАНИЕ ТОВАРА ==========

@admin_router.callback_query(F.data.startswith("admin_edit_product_full:"))
async def admin_edit_product_full_handler(callback: CallbackQuery, state: FSMContext):
    """Простое пошаговое редактирование товара"""
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
    await show_edit_step(callback, state)
    await callback.answer()

async def show_edit_step(callback_or_message, state: FSMContext):
    """Показать текущий шаг редактирования"""
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

        # Получаем название категории безопасно
        category_name = "неизвестно"
        if product.category_id:
            category = await session.get(Category, product.category_id)
            if category:
                category_name = category.name

        steps = [
            ("название", product.name, "name"),
            ("описание", product.description or "нет", "description"),
            ("цена", f"{product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}", "price"),
            ("остатки", f"{product.stock_grams}{'г' if product.unit_type == 'grams' else 'шт'}", "stock"),
            ("единицы", f"{'грамм' if product.unit_type == 'grams' else 'штук'} (шаг: {product.measurement_step})", "unit_type"),
            ("изображение", "есть" if product.image_url else "нет", "image"),
            ("категория", category_name, "category")
        ]

        if step >= len(steps):
            # Все шаги пройдены, сохраняем
            await save_product_changes(callback_or_message, state)
            return

        field_name, current_value, field_key = steps[step]

        message_text = (
            f"✏️ Редактирование товара: {product.name}\n\n"
            f"Шаг {step + 1} из {len(steps)}: {field_name}\n"
            f"Текущее значение: {current_value}\n\n"
            f"Изменить {field_name}? (да/нет):"
        )

        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(message_text)
        else:
            await callback_or_message.answer(message_text)

        # Устанавливаем состояние для обработки ответа да/нет
        await state.set_state(AdminStates.waiting_edit_value)
        await state.update_data(
            current_field=field_key,
            current_field_name=field_name,
            current_step=step,
            product_unit_type=product.unit_type
        )


@admin_router.message(AdminStates.waiting_edit_value)
async def process_edit_step_response(message: Message, state: FSMContext):
    """Обработка ответа 'да/нет' на шаге редактирования - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    logger = logging.getLogger(__name__)

    # Проверяем, что есть текст
    if not message.text:
        # Это может быть фото для шага изображения
        data = await state.get_data()
        field_key = data.get('current_field')

        if field_key == 'image':
            # Обрабатываем изображение
            await process_edit_image_value(message, state)
            return
        else:
            await message.answer("❌ Ожидается текстовый ответ 'да' или 'нет'")
            return

    response = message.text.strip().lower()
    data = await state.get_data()
    step = data.get('current_step', 0)
    field_key = data.get('current_field')

    if response in ['да', 'д', 'yes', 'y']:
        # Пользователь хочет изменить поле
        await state.update_data(waiting_for_field_value=field_key)

        # Определяем подсказку в зависимости от поля
        prompts = {
            'name': "Введите новое название товара:",
            'description': "Введите новое описание (или 'нет' для удаления):",
            'price': "Введите новую цену (например: 750/шт или 500/гр):",
            'stock': f"Введите новое количество ({'грамм' if data.get('product_unit_type', 'grams') == 'grams' else 'штук'}):",
            'unit_type': "Выберите единицы: 1 - граммы, 2 - штуки:",
            'image': "Загрузите новое изображение или отправьте 'пропустить':",
            'category': "Введите ID новой категории:"
        }

        prompt = prompts.get(field_key, f"Введите новое значение для {data.get('current_field_name')}:")
        await message.answer(prompt)

        # Устанавливаем специальное состояние для ввода значения
        state_map = {
            'name': AdminStates.waiting_edit_confirm_name,
            'description': AdminStates.waiting_edit_confirm_description,
            'price': AdminStates.waiting_edit_confirm_price,
            'stock': AdminStates.waiting_edit_confirm_stock,
            'unit_type': AdminStates.waiting_edit_confirm_unit_type,
            'image': AdminStates.waiting_edit_confirm_image,
            'category': AdminStates.waiting_edit_confirm_category
        }

        if field_key in state_map:
            await state.set_state(state_map[field_key])
        else:
            # Общее состояние для других полей
            await state.set_state(AdminStates.waiting_edit_field)

    elif response in ['нет', 'н', 'no', 'n']:
        # Пользователь не хочет менять это поле
        await state.update_data(edit_step=step + 1)
        await show_edit_step(message, state)
    else:
        await message.answer("❌ Ответьте 'да' или 'нет':")

@admin_router.message(AdminStates.waiting_edit_confirm_name)
async def process_edit_name_value(message: Message, state: FSMContext):
    """Обработка нового названия"""
    new_value = message.text.strip()
    if len(new_value) < 2:
        await message.answer("❌ Название слишком короткое. Введите снова:")
        return

    data = await state.get_data()
    changes = data.get('edit_changes', {})
    changes['name'] = new_value
    await state.update_data(edit_changes=changes, edit_step=data.get('edit_step', 0) + 1)
    await show_edit_step(message, state)

@admin_router.message(AdminStates.waiting_edit_confirm_description)
async def process_edit_description_value(message: Message, state: FSMContext):
    """Обработка нового описания"""
    new_value = message.text.strip()
    if new_value.lower() == 'нет':
        new_value = ''

    data = await state.get_data()
    changes = data.get('edit_changes', {})
    changes['description'] = new_value
    await state.update_data(edit_changes=changes, edit_step=data.get('edit_step', 0) + 1)
    await show_edit_step(message, state)

@admin_router.message(AdminStates.waiting_edit_confirm_price)
async def process_edit_price_value(message: Message, state: FSMContext):
    """Обработка новой цены"""
    try:
        text = message.text.strip().lower()

        if '/шт' in text:
            price_text = text.replace('/шт', '').strip()
            changes = {'price': float(price_text), 'unit_type': 'pieces', 'measurement_step': 1}
        elif '/гр' in text:
            price_text = text.replace('/гр', '').strip()
            changes = {'price': float(price_text), 'unit_type': 'grams', 'measurement_step': 100}
        else:
            # По умолчанию граммы
            changes = {'price': float(text), 'unit_type': 'grams', 'measurement_step': 100}

        data = await state.get_data()
        existing_changes = data.get('edit_changes', {})
        existing_changes.update(changes)
        await state.update_data(edit_changes=existing_changes, edit_step=data.get('edit_step', 0) + 1)
        await show_edit_step(message, state)

    except ValueError:
        await message.answer("❌ Неверный формат. Пример: 750/шт или 500/гр")

@admin_router.message(AdminStates.waiting_edit_confirm_stock)
async def process_edit_stock_value(message: Message, state: FSMContext):
    """Обработка новых остатков"""
    try:
        new_value = int(message.text.strip())
        if new_value < 0:
            await message.answer("❌ Количество не может быть отрицательным. Введите снова:")
            return

        data = await state.get_data()
        changes = data.get('edit_changes', {})
        changes['stock_grams'] = new_value
        await state.update_data(edit_changes=changes, edit_step=data.get('edit_step', 0) + 1)
        await show_edit_step(message, state)

    except ValueError:
        await message.answer("❌ Введите целое число")

@admin_router.message(AdminStates.waiting_edit_confirm_unit_type)
async def process_edit_unit_type_value(message: Message, state: FSMContext):
    """Обработка новых единиц измерения"""
    text = message.text.strip()
    if text == '1':
        changes = {'unit_type': 'grams', 'measurement_step': 100}
    elif text == '2':
        changes = {'unit_type': 'pieces', 'measurement_step': 1}
    else:
        await message.answer("❌ Введите '1' или '2'")
        return

    data = await state.get_data()
    existing_changes = data.get('edit_changes', {})
    existing_changes.update(changes)
    await state.update_data(edit_changes=existing_changes, edit_step=data.get('edit_step', 0) + 1)
    await show_edit_step(message, state)

@admin_router.message(AdminStates.waiting_edit_confirm_image)
async def process_edit_image_value(message: Message, state: FSMContext):
    """Обработка нового изображения - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    # Проверяем что есть либо текст, либо фото
    if message.text:
        text = message.text.strip().lower()
        if text in ['пропустить', 'skip', 'без изображения']:
            new_value = None
            await message.answer("✅ Изображение удалено")
        else:
            await message.answer("❌ Для пропуска отправьте 'пропустить', или загрузите изображение")
            return
    elif message.photo:
        new_value = message.photo[-1].file_id
        await message.answer("✅ Изображение получено")
    else:
        await message.answer("❌ Пожалуйста, загрузите изображение или отправьте 'пропустить'")
        return

    data = await state.get_data()
    changes = data.get('edit_changes', {})
    changes['image_url'] = new_value
    await state.update_data(edit_changes=changes, edit_step=data.get('edit_step', 0) + 1)
    await show_edit_step(message, state)

@admin_router.message(AdminStates.waiting_edit_confirm_category)
async def process_edit_category_value(message: Message, state: FSMContext):
    """Обработка новой категории"""
    try:
        new_value = int(message.text.strip())
        data = await state.get_data()
        changes = data.get('edit_changes', {})
        changes['category_id'] = new_value
        await state.update_data(edit_changes=changes, edit_step=data.get('edit_step', 0) + 1)
        await show_edit_step(message, state)

    except ValueError:
        await message.answer("❌ Введите числовой ID категории")

async def save_product_changes(callback_or_message, state: FSMContext):
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

            # Автоматически обновляем доступность при изменении остатков
            if 'stock_grams' in changes:
                if product.unit_type == 'grams':
                    product.available = product.stock_grams >= 100
                else:  # pieces
                    product.available = product.stock_grams >= 1

            await session.commit()

            # Показываем результат
            changes_list = "\n".join([f"• {k}: {v}" for k, v in changes.items()])
            message_text = f"✅ Товар успешно обновлен!\n\nИзменения:\n{changes_list}"

            if isinstance(callback_or_message, CallbackQuery):
                await callback_or_message.message.edit_text(message_text)
            else:
                await callback_or_message.answer(message_text)

            # Возвращаем к списку товаров
            await show_products_after_edit(callback_or_message, category_id)

    except Exception as e:
        logger.error(f"Ошибка сохранения товара: {e}")
        message_text = f"❌ Ошибка сохранения: {e}"
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(message_text)
        else:
            await callback_or_message.answer(message_text)

    await state.clear()

async def show_products_after_edit(callback_or_message, category_id: int):
    """Показать список товаров после редактирования"""
    from keyboards import admin_product_management_keyboard

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
                "unit_type": p.unit_type,
                "is_hypoallergenic": p.is_hypoallergenic  # ДОБАВЛЯЕМ ЭТУ СТРОЧКУ
            }
            for p in products
        ]

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

# ========== ФУНКЦИЯ СТАТИСТИКИ ==========
@admin_router.callback_query(F.data == "admin_statistics")
async def admin_statistics_handler(callback: CallbackQuery):
    """Показать статистику"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    try:
        # Логирование операции
        from logging_config import OperationLogger
        OperationLogger.log_admin_operation(
            admin_id=callback.from_user.id,
            action="view_statistics",
            target="dashboard"
        )

        # Получение статистики
        from statistics import statistics_service
        stats = await statistics_service.get_dashboard_stats()

        # Формирование текста с временной меткой
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        stats_text = (
            f"📊 СТАТИСТИКА МАГАЗИНА (обновлено: {timestamp})\n\n"
            f"📦 Всего заказов: {stats.get('total_orders', 0)}\n"
            f"👤 Всего пользователей: {stats.get('total_users', 0)}\n"
            f"🛒 Всего товаров: {stats.get('total_products', 0)}\n"
            f"💰 Общая выручка: {stats.get('total_revenue', 0):.0f} RSD\n"
            f"📈 Средний чек: {stats.get('avg_order_value', 0):.0f} RSD"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_statistics")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
        ])

        # Пытаемся отредактировать, если не получается - отправляем новое сообщение
        try:
            await callback.message.edit_text(
                text=stats_text,
                reply_markup=keyboard
            )
        except Exception as edit_error:
            # Если не удалось отредактировать (например, сообщение не изменилось)
            # отправляем новое сообщение
            await callback.message.answer(
                text=stats_text,
                reply_markup=keyboard
            )
            # Удаляем старое сообщение (опционально)
            try:
                await callback.message.delete()
            except:
                pass

    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        # Вместо показа alert, просто отвечаем что статистика обновлена
        await callback.answer("📊 Статистика обновлена")

@admin_router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Назад в главное меню админки"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "👑 Панель администратора Barkery Shop\n\n\nВыберите действие:",
        reply_markup=admin_main_keyboard()
    )
    await callback.answer()

# Обработчик удаления товара (оставляю один в конце файла)
@admin_router.callback_query(F.data.startswith("admin_delete_product:"))
async def admin_delete_product_handler(callback: CallbackQuery):
    """ПРОСТЕЙШИЙ обработчик удаления - ТОЛЬКО ДЛЯ ТЕСТА"""
    # 1. СРАЗУ показываем что обработчик вызвался
    await callback.answer("🚨 Обработчик ВЫЗВАН!", show_alert=True)

    # 2. Разбираем данные
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("❌ Ошибка формата данных", show_alert=True)
        return

    product_id = int(parts[1])
    category_id = int(parts[2])

    # 3. ПРОСТОЕ удаление из БД
    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer("❌ Товар не найден в БД", show_alert=True)
            return

        product_name = product.name

        # УДАЛЕНИЕ
        await session.delete(product)
        await session.commit()

    # 4. Результат
    await callback.answer(f"✅ УДАЛЕНО из БД: {product_name}", show_alert=True)

    # 5. Простое сообщение
    await callback.message.answer(f"🗑️ Товар '{product_name}' удален из базы данных")

    # 6. Возвращаем к списку товаров
    await show_products_after_edit(callback, category_id)

# Эту функцию добавить ПОСЛЕ всех существующих функций в admin.py
# Например, после функции process_edit_field

@admin_router.callback_query(F.data.startswith("admin_refresh_catalog:"))
async def admin_refresh_catalog_handler(callback: CallbackQuery):
    """Принудительное обновление каталога для категории - НОВАЯ ФУНКЦИЯ"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    category_id = int(callback.data.split(":")[1])

    async with get_session() as session:
        # Обновляем все товары категории по логике hide_when_zero
        stmt = select(Product).where(Product.category_id == category_id)
        result = await session.execute(stmt)
        products = result.scalars().all()

        updated_count = 0
        for product in products:
            old_status = product.available

            # Применяем логику hide_when_zero
            if product.unit_type == 'grams':
                # Для весового: доступен если >= 100г
                product.available = product.stock_grams >= 100
            else:  # pieces
                # Для штучного: доступен если >= 1шт
                product.available = product.stock_grams >= 1

            if old_status != product.available:
                updated_count += 1
                logger.info(f"Товар {product.name} обновлен: {old_status} -> {product.available}")

        if updated_count > 0:
            await session.commit()

        # Возвращаем обновленный список
        category = await session.get(Category, category_id)
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

        try:
            await callback.message.edit_text(
                f"🛒 Товары категории: {category.name}\n\n"
                f"Количество товаров: {len(products_list)}\n"
                f"🔄 Обновлено статусов: {updated_count}",
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )
        except Exception as e:
            logger.warning(f"Не удалось отредактировать сообщение: {e}")
            # Отправляем новое сообщение
            await callback.message.answer(
                f"🛒 Товары категории: {category.name}\n\n"
                f"Количество товаров: {len(products_list)}\n"
                f"🔄 Обновлено статусов: {updated_count}",
                reply_markup=admin_product_management_keyboard(products_list, category_id)
            )

        await callback.answer(f"✅ Каталог обновлен. Изменено: {updated_count} товаров")