"""
\nАдминка Barkery Shop (полная исправленная версия)
\nВерсия с исправленной логикой уведомлений
\n"""
\nimport logging
\nfrom aiogram import Router, F
\nfrom aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
\nfrom aiogram.filters import Command
\nfrom aiogram.fsm.context import FSMContext
\nfrom aiogram.fsm.state import State, StatesGroup
\nfrom sqlalchemy import select, func
\nfrom database import get_session, Product, Category, CartItem, User
\nfrom config import settings
\nfrom keyboards import admin_main_keyboard, admin_categories_keyboard, admin_products_keyboard, admin_product_management_keyboard
\n
\nlogger = logging.getLogger(__name__)
\nadmin_router = Router()
\n
\nasync def is_admin(user_id: int) -> bool:
\n    return user_id == settings.admin_id
\n
\n
\nasync def check_and_notify_out_of_stock(bot, product_id, product_name, ordering_user_id=None):
\n    """Заглушка для функции уведомления о закончившемся товаре"""
\n    logger = logging.getLogger(__name__)
\n    logger.info(f"Товар закончился: {product_name} (ID: {product_id})")
\n    # В реальной реализации здесь была бы логика уведомления
\n    return 0  # Возвращаем 0 уведомленных пользователей
\n
\nclass AdminStates(StatesGroup):
\n    waiting_category_name = State()
\n    waiting_edit_category_name = State()
\n    waiting_product_name = State()
\n    waiting_product_description = State()
\n    waiting_product_price = State()
\n    waiting_product_stock = State()
\n    waiting_product_unit_type = State()
\n    waiting_product_image = State()
\n    waiting_product_category = State()
\n    waiting_edit_field = State()
\n    waiting_edit_description = State()
\n    waiting_edit_confirm_name = State()
\n    waiting_edit_confirm_description = State()
\n    waiting_edit_confirm_price = State()
\n    waiting_edit_confirm_stock = State()
\n    waiting_edit_confirm_unit_type = State()
\n    waiting_edit_confirm_image = State()
\n    waiting_edit_confirm_category = State()
\n    waiting_edit_final_save = State()
\n    waiting_edit_value = State()
\n
\n
\n# Главная админ панель
\n@admin_router.message(Command("admin"))
\nasync def admin_panel(message: Message):
\n    """Панель администратора"""
\n    if not await is_admin(message.from_user.id):
\n        await message.answer("❌ Доступ запрещен")
\n        return
\n    await message.answer(
\n            "👑 Панель администратора Barkery Shop\n\n\n"
\n            "Выберите действие:",
\n        reply_markup=admin_main_keyboard()
\n    )
\n
\n# Управление категориями
\n@admin_router.callback_query(F.data == "admin_categories")
\nasync def admin_categories(callback: CallbackQuery):
\n    """Управление категориями"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    async with get_session() as session:
\n        stmt = select(Category).order_by(Category.name)
\n        result = await session.execute(stmt)
\n        categories = result.scalars().all()
\n        if not categories:
\n            await callback.message.edit_text(
\n                "📦 Управление категориями\n\n"
\n                "Категорий нет. Добавьте первую категорию!",
\n                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
\n                    [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_add_category")],
\n                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
\n                ])
\n            )
\n            return
\n        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
\n        await callback.message.edit_text(
\n            "📦 Управление категориями\n\n"
\n            f"Всего категорий: {len(categories_list)}",
\n            reply_markup=admin_categories_keyboard(categories_list)
\n        )
\n    await callback.answer()
\n
\n# Добавление категории
\n@admin_router.callback_query(F.data == "admin_add_category")
\nasync def admin_add_category_handler(callback: CallbackQuery, state: FSMContext):
\n    """Добавление категории"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    await state.set_state(AdminStates.waiting_category_name)
\n    await callback.message.edit_text(
\n        "➕ Добавление новой категории\n\n"
\n        "Введите название категории:"
\n    )
\n    await callback.answer()
\n
\n@admin_router.message(AdminStates.waiting_category_name)
\nasync def process_category_name(message: Message, state: FSMContext):
\n    """Обработка названия категории"""
\n    category_name = message.text.strip()
\n    if not category_name or len(category_name) < 2:
\n        await message.answer("❌ Название слишком короткое. Введите снова:")
\n        return
\n    async with get_session() as session:
\n        # Проверяем существование категории
\n        stmt = select(Category).where(Category.name == category_name)
\n        result = await session.execute(stmt)
\n        existing = result.scalar_one_or_none()
\n        if existing:
\n            await message.answer("❌ Категория с таким названием уже существует. Введите другое:")
\n            return
\n        # Создаем категорию
\n        category = Category(name=category_name)
\n        session.add(category)
\n        await session.commit()
\n        await session.refresh(category)
\n        await message.answer(f"✅ Категория '{category_name}' успешно создана! ID: {category.id}")
\n        await state.clear()
\n        # Возвращаем к списку категорий
\n        stmt = select(Category).order_by(Category.name)
\n        result = await session.execute(stmt)
\n        categories = result.scalars().all()
\n        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
\n        from keyboards import admin_categories_keyboard
\n        await message.answer(
\n            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
\n            reply_markup=admin_categories_keyboard(categories_list)
\n        )
\n
\n# Редактирование категории
\n@admin_router.callback_query(F.data.startswith("admin_edit_category:"))
\nasync def admin_edit_category_handler(callback: CallbackQuery, state: FSMContext):
\n    """Редактирование категории"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    category_id = int(callback.data.split(":")[1])
\n    await state.update_data(edit_category_id=category_id)
\n    await state.set_state(AdminStates.waiting_edit_category_name)
\n    async with get_session() as session:
\n        category = await session.get(Category, category_id)
\n        if category:
\n            await callback.message.edit_text(
\n                f"✏️ Редактирование категории\n\n"
\n                f"Текущее название: {category.name}\n\n"
\n                "Введите новое название категории:"
\n            )
\n    await callback.answer()
\n
\n@admin_router.message(AdminStates.waiting_edit_category_name)
\nasync def process_edit_category_name(message: Message, state: FSMContext):
\n    """Обработка нового названия категории"""
\n    new_name = message.text.strip()
\n    if len(new_name) < 2:
\n        await message.answer("❌ Название слишком короткое. Введите снова:")
\n        return
\n    data = await state.get_data()
\n    category_id = data.get("edit_category_id")
\n    async with get_session() as session:
\n        category = await session.get(Category, category_id)
\n        if not category:
\n            await message.answer("❌ Категория не найдена")
\n            await state.clear()
\n            return
\n        # Проверяем нет ли другой категории с таким названием
\n        stmt = select(Category).where(Category.name == new_name, Category.id != category_id)
\n        result = await session.execute(stmt)
\n        existing = result.scalar_one_or_none()
\n        if existing:
\n            await message.answer("❌ Категория с таким названием уже существует. Введите другое:")
\n            return
\n        old_name = category.name
\n        category.name = new_name
\n        await session.commit()
\n        await message.answer(f"✅ Категория переименована: {old_name} → {new_name}")
\n        # Возвращаем к списку категорий
\n        stmt = select(Category).order_by(Category.name)
\n        result = await session.execute(stmt)
\n        categories = result.scalars().all()
\n        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
\n        from keyboards import admin_categories_keyboard
\n        await message.answer(
\n            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
\n            reply_markup=admin_categories_keyboard(categories_list)
\n        )
\n    await state.clear()
\n
\n# Удаление категории
\n@admin_router.callback_query(F.data.startswith("admin_delete_category:"))
\nasync def admin_delete_category_handler(callback: CallbackQuery):
\n    """Удаление категории"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    category_id = int(callback.data.split(":")[1])
\n    async with get_session() as session:
\n        category = await session.get(Category, category_id)
\n        if not category:
\n            await callback.answer("❌ Категория не найдена", show_alert=True)
\n            return
\n        # Проверяем есть ли товары в категории
\n        stmt = select(Product).where(Product.category_id == category_id)
\n        result = await session.execute(stmt)
\n        products = result.scalars().all()
\n        if products:
\n            await callback.answer(
\n                f"❌ Нельзя удалить категорию с товарами. Сначала удалите {len(products)} товар(ов)",
\n                show_alert=True
\n            )
\n            return
\n        # Удаляем категорию
\n        await session.delete(category)
\n        await session.commit()
\n        await callback.answer(f"✅ Категория '{category.name}' удалена")
\n        # Обновляем список категорий
\n        stmt = select(Category).order_by(Category.name)
\n        result = await session.execute(stmt)
\n        categories = result.scalars().all()
\n        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
\n        await callback.message.edit_text(
\n            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
\n            reply_markup=admin_categories_keyboard(categories_list)
\n        )
\n
\n# Управление товарами
\n@admin_router.callback_query(F.data == "admin_products")
\nasync def admin_products(callback: CallbackQuery):
\n    """Управление товарами"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    async with get_session() as session:
\n        stmt = select(Category).order_by(Category.name)
\n        result = await session.execute(stmt)
\n        categories = result.scalars().all()
\n        if not categories:
\n            await callback.message.edit_text(
\n                "🛒 Управление товарами\n\n"
\n                "Сначала создайте категории.",
\n                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
\n                    [InlineKeyboardButton(text="📦 К категориям", callback_data="admin_categories")],
\n                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")]
\n                ])
\n            )
\n            return
\n        await callback.message.edit_text(
\n            "🛒 Управление товарами\n\n"
\n            f"Выберите категорию:",
\n            reply_markup=admin_products_keyboard(categories)
\n        )
\n    await callback.answer()
\n
\n# Товары в выбранной категории
\n@admin_router.callback_query(F.data.startswith("admin_category_products:"))
\nasync def admin_category_products_handler(callback: CallbackQuery):
\n    """Товары в выбранной категории"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    category_id = int(callback.data.split(":")[1])
\n    async with get_session() as session:
\n        category = await session.get(Category, category_id)
\n        if not category:
\n            await callback.answer("❌ Категория не найдена", show_alert=True)
\n            return
\n        stmt = select(Product).where(Product.category_id == category_id)
\n        result = await session.execute(stmt)
\n        products = result.scalars().all()
\n        products_list = [
\n            {
\n                "id": p.id,
\n                "name": p.name,
\n                "price": p.price,
\n                "stock_grams": p.stock_grams,
\n                "available": p.available
\n            }
\n            for p in products
\n        ]
\n        await callback.message.edit_text(
\n            f"🛒 Товары категории: {category.name}\n\n"
\n            f"Количество товаров: {len(products_list)}",
\n            reply_markup=admin_product_management_keyboard(products_list, category_id)
\n        )
\n    await callback.answer()
\n
\n# Добавление товара - исправленная версия
\n@admin_router.callback_query(F.data == "admin_add_product")
\nasync def admin_add_product_handler(callback: CallbackQuery, state: FSMContext):
\n    """Добавление товара - исправленная версия"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    
\n    # Получаем список категорий
\n    async with get_session() as session:
\n        stmt = select(Category).order_by(Category.name)
\n        result = await session.execute(stmt)
\n        categories = result.scalars().all()
\n    
\n    if not categories:
\n        await callback.answer("❌ Нет категорий. Сначала создайте категорию.", show_alert=True)
\n        return
\n    
\n    await state.update_data(available_categories=categories)
\n    await state.set_state(AdminStates.waiting_product_name)
\n    
\n    categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
\n    await callback.message.edit_text(
\n        "➕ Добавление нового товара\n\n"
\n        f"Доступные категории:\n{categories_text}\n\n"
\n        "Шаг 1 из 6: Введите название товара:"
\n    )
\n    await callback.answer()
\n
\n@admin_router.message(AdminStates.waiting_product_name)
\nasync def process_product_name_create(message: Message, state: FSMContext):
\n    """Обработка названия нового товара"""
\n    product_name = message.text.strip()
\n    if len(product_name) < 2:
\n        await message.answer("❌ Название слишком короткое. Введите снова:")
\n        return
\n    
\n    await state.update_data(product_name=product_name)
\n    await state.set_state(AdminStates.waiting_product_description)
\n    await message.answer(
\n        f"✅ Название принято: {product_name}\n\n"
\n        "Шаг 2 из 6: Введите описание товара (или 'нет' если без описания):"
\n    )
\n
\n@admin_router.message(AdminStates.waiting_product_description)
\nasync def process_product_description_create(message: Message, state: FSMContext):
\n    """Обработка описания нового товара"""
\n    description = message.text.strip()
\n    if description.lower() == 'нет':
\n        description = ''
\n    
\n    await state.update_data(description=description)
\n    await state.set_state(AdminStates.waiting_product_price)
\n    await message.answer(
\n        f"✅ Описание принято\n\n"
\n        "Шаг 3 из 6: Введите цену в формате цена/шт или цена/гр:\n"
\n        "Пример для штучного товара: 750/шт\n"
\n        "Пример для весового товара: 500/гр"
\n    )
\n
\n@admin_router.message(AdminStates.waiting_product_price)
\nasync def process_product_price_create(message: Message, state: FSMContext):
\n    """Обработка цены нового товара с определением единиц измерения"""
\n    try:
\n        text = message.text.strip().lower()
\n        
\n        # Определяем единицы измерения
\n        if '/шт' in text:
\n            # Товар штучный
\n            price_text = text.replace('/шт', '').strip()
\n            unit_type = 'pieces'
\n            measurement_step = 1
\n            unit_text = 'штук'
\n            price_label = 'RSD/шт'
\n        elif '/гр' in text:
\n            # Товар весовой
\n            price_text = text.replace('/гр', '').strip()
\n            unit_type = 'grams'
\n            measurement_step = 100
\n            unit_text = 'грамм'
\n            price_label = 'RSD/100г'
\n        else:
\n            # По умолчанию - граммы (для обратной совместимости)
\n            price_text = text
\n            unit_type = 'grams'
\n            measurement_step = 100
\n            unit_text = 'грамм'
\n            price_label = 'RSD/100г'
\n        
\n        price = float(price_text)
\n        if price <= 0:
\n            await message.answer("❌ Цена должна быть больше 0. Введите снова:")
\n            return
\n
\n        await state.update_data(
\n            price=price,
\n            unit_type=unit_type,
\n            measurement_step=measurement_step
\n        )
\n        
\n        # Пропускаем шаг выбора единиц измерения
\n        await state.set_state(AdminStates.waiting_product_stock)
\n        await message.answer(
\n            f"✅ Цена принята: {price} {price_label}\n"
\n            f"✅ Единицы измерения: {unit_text} (шаг: {measurement_step})\n\n"
\n            "Шаг 4 из 6: Введите количество (только число):\n"
\n            f"Для {unit_text}: {1000 if unit_type == 'grams' else 50} "
\n            f"(это {1000 if unit_type == 'grams' else 50} {unit_text})"
\n        )
\n    except ValueError:
\n        await message.answer(
\n            "❌ Введите число в формате: цена/шт или цена/гр\n\n"
\n            "Пример: 750/шт или 500/гр")
\n
\n@admin_router.message(AdminStates.waiting_product_stock)\nasync def process_product_stock_create(message: Message, state: FSMContext):\n    """Обработка количества для нового товара"""\n    try:\n        stock = int(message.text.strip())\n        if stock < 0:\n            await message.answer("❌ Количество не может быть отрицательным. Введите снова:")\n            return\n\n        await state.update_data(stock=stock)\n        \n        # Получаем данные из состояния для отображения правильных единиц\n        data = await state.get_data()\n        unit_type = data.get('unit_type', 'grams')\n        measurement_step = data.get('measurement_step', 100)\n        unit_text = 'грамм' if unit_type == 'grams' else 'штук'\n        \n        # Пропускаем шаг выбора единиц (они уже определены при вводе цены)\n        await state.set_state(AdminStates.waiting_product_image)\n        \n        await message.answer(\n            f"✅ Количество принято: {stock} {unit_text}\n"\n            f"✅ Единицы измерения: {unit_text} (шаг: {measurement_step})\n\n"\n            "Шаг 5 из 6: Загрузите изображение товара.\n"\n            "Или отправьте 'пропустить' если без изображения:"\n        )\n    except ValueError:\n        await message.answer("❌ Введите число. Введите снова:")\n@admin_router.message(AdminStates.waiting_product_unit_type)
\n"
\n        "Шаг 6 из 6: Загрузите изображение товара.\n"
\n        "Или отправьте 'пропустить' если без изображения:"
\n    )
\n
\n@admin_router.message(AdminStates.waiting_product_image)
\nasync def process_product_image(message: Message, state: FSMContext):
\n    """Обработка изображения товара"""
\n    image_url = None
\n
\n    if message.text and message.text.strip().lower() in ['пропустить', 'skip', 'без изображения']:
\n        await message.answer("✅ Пропускаем загрузку изображения")
\n    elif message.photo:
\n        # Используем file_id от телеграма
\n        image_url = message.photo[-1].file_id
\n        await message.answer(f"✅ Изображение получено")
\n    else:
\n        await message.answer("❌ Пожалуйста, загрузите изображение или отправьте 'пропустить'")
\n        return
\n
\n    await state.update_data(image_url=image_url)
\n
\n    # Получаем список категорий из состояния
\n    data = await state.get_data()
\n    categories = data.get('available_categories', [])
\n
\n    if not categories:
\n        # Если категории утеряны, получаем их заново из БД
\n        from database import get_session, Category
\n        from sqlalchemy import select
\n        
\n        async with get_session() as session:
\n            stmt = select(Category).order_by(Category.name)
\n            result = await session.execute(stmt)
\n            categories = result.scalars().all()
\n            
\n            if categories:
\n                # Сохраняем в состоянии
\n                await state.update_data(available_categories=categories)
\n                categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
\n                
\n                await state.set_state(AdminStates.waiting_product_category)
\n                await message.answer(
\n                    f"✅ Изображение обработано\n\n"
\n                    f"Доступные категории:\n{categories_text}\n\n"
\n                    "Шаг 6 из 6: Введите ID категории для товара:"
\n                )
\n                return
\n            else:
\n                await message.answer("❌ В базе данных нет категорий. Сначала создайте категории.")
\n                await state.clear()
\n                return
\n
\n    # Если категории есть, продолжаем как обычно
\n    categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
\n    await state.set_state(AdminStates.waiting_product_category)
\n
\n    await message.answer(
\n        f"✅ Изображение обработано\n\n"
\n        f"Доступные категории:\n{categories_text}\n\n"
\n        "Шаг 6 из 6: Введите ID категории для товара:"
\n    )
\n
\n@admin_router.message(AdminStates.waiting_product_category)
\nasync def process_product_category(message: Message, state: FSMContext):
\n    """Обработка категории товара"""
\n    try:
\n        category_id = int(message.text.strip())
\n        
\n        # Получаем данные из состояния
\n        data = await state.get_data()
\n        categories = data.get('available_categories', [])
\n        
\n        # Проверяем существование категории
\n        category_exists = False
\n        for cat in categories:
\n            if cat.id == category_id:
\n                category_exists = True
\n                break
\n        
\n        if not category_exists:
\n            await message.answer(f"❌ Категория с ID {category_id} не найдена. Введите ID из списка:")
\n            return
\n        
\n        # Создаем товар
\n        async with get_session() as session:
\n            # Проверяем наличие всех необходимых данных
\n            required_fields = ['product_name', 'price', 'stock', 'unit_type', 'measurement_step', 'category_id']
\n            missing = []
\n            for field in required_fields:
\n                if field not in data:
\n                    missing.append(field)
\n            
\n            if missing:
\n                await message.answer(f"❌ Ошибка: отсутствуют данные: {missing}")
\n                await state.clear()
\n                return
\n            
\n            product = Product(
\n                name=data['product_name'],
\n                description=data.get('description', ''),
\n                price=data['price'],
\n                stock_grams=data['stock'],
\n                image_url=data.get('image_url'),
\n                unit_type=data.get('unit_type', 'grams'),
\n                measurement_step=data.get('measurement_step', 100),
\n                available=True,
\n                is_active=True,
\n                category_id=category_id
\n            )
\n            
\n            session.add(product)
\n            await session.commit()
\n            await session.refresh(product)
\n        
\n        await message.answer(
\n            f"✅ Товар успешно создан!\n\n"
\n            f"Название: {product.name}\n"
\n            f"Цена: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n"
\n            f"Количество: {product.stock_grams} ({'грамм' if product.unit_type == 'grams' else 'штук'})\n"
\n            f"Категория ID: {product.category_id}\n"
\n            f"Товар ID: {product.id}"
\n        )
\n        
\n        # Возвращаем к списку товаров
\n        await state.clear()
\n        from keyboards import admin_main_keyboard
\n        await message.answer(
\n            "👑 Панель администратора\n\nВыберите действие:",
\n            reply_markup=admin_main_keyboard()
\n        )
\n        
\n    except ValueError:
\n        await message.answer("❌ Введите число (ID категории):")
\n    except Exception as e:
\n        logger.error(f"Ошибка создания товара: {e}")
\n        logger.error(f"Данные в состоянии: {data}")
\n        import traceback
\n        logger.error(f"Трассировка: {traceback.format_exc()}")
\n        await message.answer(f"❌ Ошибка при создании товара: {str(e)}")
\n        await state.clear()
\n
\n@admin_router.callback_query(F.data.startswith("admin_toggle_product:"))
\nasync def admin_toggle_product_handler(callback: CallbackQuery):
\n    """Включение/выключение товара"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if not product:
\n            await callback.answer("❌ Товар не найден", show_alert=True)
\n            return
\n        product.available = not product.available
\n        await session.commit()
\n        status = "включен" if product.available else "выключен"
\n        await callback.answer(f"✅ Товар '{product.name}' {status}")
\n        # Обновляем список товаров
\n        category = await session.get(Category, category_id)
\n        stmt = select(Product).where(Product.category_id == category_id)
\n        result = await session.execute(stmt)
\n        products = result.scalars().all()
\n        products_list = [
\n            {
\n                "id": p.id,
\n                "name": p.name,
\n                "price": p.price,
\n                "stock_grams": p.stock_grams,
\n                "available": p.available
\n            }
\n            for p in products
\n        ]
\n        await callback.message.edit_text(
\n            f"🛒 Товары категории: {category.name}\n\n"
\n            f"Количество товаров: {len(products_list)}",
\n            reply_markup=admin_product_management_keyboard(products_list, category_id)
\n        )
\n
\n# Обновление остатков товара
\n@admin_router.callback_query(F.data.startswith("admin_update_stock:"))
\nasync def admin_update_stock_handler(callback: CallbackQuery, state: FSMContext):
\n    """Обновление остатков товара с проверкой корзин пользователей"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n    
\n    await state.update_data(
\n        product_id=product_id,
\n        category_id=category_id
\n    )
\n    await state.set_state(AdminStates.waiting_edit_field)
\n    
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if product:
\n            # Проверяем есть ли этот товар в корзинах пользователей
\n            stmt = select(func.sum(CartItem.quantity)).where(
\n                CartItem.product_id == product_id
\n            )
\n            result = await session.execute(stmt)
\n            in_carts = result.scalar() or 0
\n            
\n            await state.update_data(edit_field='stock_grams')
\n            
\n            if in_carts > 0:
\n                warning = f"⚠️ Внимание: этот товар есть в корзинах у пользователей ({in_carts}{'г' if product.unit_type == 'grams' else 'шт'})\n"
\n            else:
\n                warning = ""
\n            
\n            await callback.message.edit_text(
\n                f"📦 Обновление остатков\n\n"
\n                f"Товар: {product.name}\n"
\n                f"Текущие остатки: {product.stock_grams}{'г' if product.unit_type == 'grams' else 'шт'}\n"
\n                f"{warning}\n"
\n                "Введите новое количество:"
\n            )
\n        else:
\n            await callback.message.edit_text(
\n                "📦 Обновление остатков\n\n"
\n                "Введите новое количество:"
\n            )
\n    await callback.answer()
\n
\n# Редактирование названия товара
\n@admin_router.callback_query(F.data.startswith("admin_edit_product_name:"))
\nasync def admin_edit_product_name_handler(callback: CallbackQuery, state: FSMContext):
\n    """Редактирование названия товара"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n    await state.update_data(
\n        product_id=product_id,
\n        category_id=category_id,
\n        edit_field='name'
\n    )
\n    await state.set_state(AdminStates.waiting_edit_field)
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if product:
\n            await callback.message.edit_text(
\n                f"✏️ Редактирование названия\n\n"
\n                f"Товар: {product.name}\n"
\n                f"Текущее название: {product.name}\n\n"
\n                "Введите новое название товара:"
\n            )
\n        else:
\n            await callback.message.edit_text(
\n                f"✏️ Редактирование названия\n\n"
\n                "Введите новое название товара:"
\n            )
\n    await callback.answer()
\n
\n# Редактирование цены товара
\n@admin_router.callback_query(F.data.startswith("admin_edit_product_price:"))
\nasync def admin_edit_product_price_handler(callback: CallbackQuery, state: FSMContext):
\n    """Редактирование цены товара"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n    await state.update_data(
\n        product_id=product_id,
\n        category_id=category_id,
\n        edit_field='price'
\n    )
\n    await state.set_state(AdminStates.waiting_edit_field)
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if product:
\n            await callback.message.edit_text(
\n                f"💰 Редактирование цены\n\n"
\n                f"Товар: {product.name}\n"
\n                f"Текущая цена: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n\n"
\n                "Введите новую цены:"
\n            )
\n        else:
\n            await callback.message.edit_text(
\n                f"💰 Редактирование цены\n\n"
\n                "Введите новую цены:"
\n            )
\n    await callback.answer()
\n
\n# Редактирование единиц измерения товара
\n
\n# Редактирование описания товара
\n@admin_router.callback_query(F.data.startswith("admin_edit_product_description:"))
\nasync def admin_edit_product_description_handler(callback: CallbackQuery, state: FSMContext):
\n    """Редактирование описания товара"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n    await state.update_data(
\n        product_id=product_id,
\n        category_id=category_id,
\n        edit_field='description'
\n    )
\n    await state.set_state(AdminStates.waiting_edit_field)
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if product:
\n            current_desc = product.description or "нет описания"
\n            await callback.message.edit_text(
\n                f"📝 Редактирование описания\n\n"
\n                f"Товар: {product.name}\n"
\n                f"Текущее описание: {current_desc}\n\n"
\n                "Введите новое описание товара (или 'нет' для удаления):"
\n            )
\n        else:
\n            await callback.message.edit_text(
\n                f"📝 Редактирование описания\n\n"
\n                "Введите новое описание товара (или 'нет' для удаления):"
\n            )
\n    await callback.answer()
\n@admin_router.callback_query(F.data.startswith("admin_edit_product_units:"))
\nasync def admin_edit_product_units_handler(callback: CallbackQuery, state: FSMContext):
\n    """Редактирование единиц измерения товара - исправленная версия"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n    
\n    # Устанавливаем состояние для редактирования единиц
\n    await state.update_data(
\n        product_id=product_id,
\n        category_id=category_id,
\n        edit_field='unit_type'
\n    )
\n    
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if product:
\n            current_unit = "грамм" if product.unit_type == 'grams' else "штук"
\n            await callback.message.edit_text(
\n                f"📏 Редактирование единиц измерения\n\n"
\n                f"Товар: {product.name}\n"
\n                f"Текущие единицы: {current_unit} (шаг: {product.measurement_step})\n\n"
\n                "Выберите новые единицы измерения товара:\n"
\n                "1. Граммы (измеряется в граммах, шаг 100г)\n"
\n                "2. Штуки (измеряется в штуках, шаг 1шт)\n\n"
\n                "Введите '1' или '2':"
\n            )
\n        else:
\n            await callback.message.edit_text(
\n                f"📏 Редактирование единиц измерения\n\n"
\n                "Выберите единицы измерения товара:\n"
\n                "1. Граммы (измеряется в граммах, шаг 100г)\n"
\n                "2. Штуки (измеряется в штуках, шаг 1шт)\n\n"
\n                "Введите '1' или '2':"
\n            )
\n    
\n    await state.set_state(AdminStates.waiting_edit_field)
\n    await callback.answer()
\n
\n@admin_router.message(AdminStates.waiting_edit_field)
\nasync def process_edit_field(message: Message, state: FSMContext):
\n    """Обработка изменения поля товара"""
\n    logger = logging.getLogger(__name__)
\n    try:
\n        data = await state.get_data()
\n        field = data.get('edit_field')
\n        product_id = data.get('product_id')
\n        category_id = data.get('category_id')
\n        
\n        if not all([field, product_id, category_id]):
\n            await message.answer("❌ Ошибка данных. Попробуйте снова.")
\n            await state.clear()
\n            return
\n        
\n        value = message.text.strip()
\n        
\n        async with get_session() as session:
\n            product = await session.get(Product, product_id)
\n            if not product:
\n                await message.answer("❌ Товар не найден")
\n                await state.clear()
\n                return
\n            
\n            # Преобразуем значение в нужный тип
\n            if field == 'stock_grams':
\n                new_value = int(value)
\n                if new_value < 0:
\n                    await message.answer("❌ Количество не может быть отрицательным. Введите снова:")
\n                    return
\n                old_value = product.stock_grams
\n                product.stock_grams = new_value
\n
\n                # Логика возврата товара в доступность при достаточных остатках
\n                if not product.available:
\n                    should_show = False
\n                    if product.unit_type == 'grams':
\n                        # Для весового: показываем если >= 100г
\n                        if new_value >= 100:
\n                            should_show = True
\n                            reason = "остатки восстановлены до 100г и более"
\n                    else:  # pieces
\n                        # Для штучный: показываем если >= 1шт
\n                        if new_value >= 1:
\n                            should_show = True
\n                            reason = "остатки восстановлены до 1шт и более"
\n
\n                    if should_show:
\n                        product.available = True
\n                        logger.info(f"Товар {product.name} (ID: {product.id}) возвращен в доступность: {reason}")
\n            elif field == 'price':
\n                new_value = float(value)
\n                if new_value <= 0:
\n                    await message.answer("❌ Цена должна быть больше 0. Введите снова:")
\n                    return
\n                old_value = product.price
\n                product.price = new_value
\n            elif field == 'name':
\n                if len(value) < 2:
\n                    await message.answer("❌ Название слишком короткое. Введите снова:")
\n                    return
\n                old_value = product.name
\n                product.name = value
\n            elif field == 'description':
\n                if value.lower() == 'нет':
\n                    value = ''
\n                old_value = product.description
\n                product.description = value
\n            elif field == 'unit_type':
\n                if value == '1':
\n                    unit_type = 'grams'
\n                    measurement_step = 100
\n                elif value == '2':
\n                    unit_type = 'pieces'
\n                    measurement_step = 1
\n                else:
\n                    await message.answer("❌ Введите '1' или '2':")
\n                    return
\n                
\n                old_value = product.unit_type
\n                product.unit_type = unit_type
\n                product.measurement_step = measurement_step
\n                
\n                # Обновляем текст для сообщения об успехе
\n                unit_text = 'грамм' if unit_type == 'grams' else 'штук'
\n                value = f"{unit_text} (шаг: {measurement_step})"
\n            else:
\n                await message.answer("❌ Неизвестное поле для редактирования")
\n                await state.clear()
\n                return
\n            
\n            await session.commit()
\n            await message.answer(f"✅ Товар обновлен: {field} = {value}")
\n            
\n            # Возвращаем к списку товаров
\n            category = await session.get(Category, category_id)
\n            stmt = select(Product).where(Product.category_id == category_id)
\n            result = await session.execute(stmt)
\n            products = result.scalars().all()
\n            products_list = [
\n                {
\n                    "id": p.id,
\n                    "name": p.name,
\n                    "price": p.price,
\n                    "stock_grams": p.stock_grams,
\n                    "available": p.available
\n                }
\n                for p in products
\n            ]
\n            await message.answer(
\n                f"🛒 Товары категории: {category.name}\n\n"
\n                f"Количество товаров: {len(products_list)}",
\n                reply_markup=admin_product_management_keyboard(products_list, category_id)
\n            )
\n        
\n        await state.clear()
\n        
\n    except ValueError:
\n        await message.answer("❌ Неверный формат. Введите число:")
\n    except Exception as e:
\n        logger.error(f"Ошибка обновления товара: {e}")
\n        await message.answer("❌ Ошибка обновления товара")
\n        await state.clear()
\n
\n# Удаление товара
\n
\n# ========== ПРОСТОЕ ПОШАГОВОЕ РЕДАКТИРОВАНИЕ ==========
\n
\n@admin_router.callback_query(F.data.startswith("admin_edit_product_full:"))
\nasync def admin_edit_product_full_handler(callback: CallbackQuery, state: FSMContext):
\n    """Простое пошаговое редактирование товара"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n
\n    parts = callback.data.split(":")
\n    product_id = int(parts[1])
\n    category_id = int(parts[2])
\n
\n    await state.update_data(
\n        edit_product_id=product_id,
\n        edit_category_id=category_id,
\n        edit_step=0,
\n        edit_changes={}
\n    )
\n
\n    # Показываем первый шаг
\n    await show_edit_step(callback, state)
\n    await callback.answer()
\n
\nasync def show_edit_step(callback_or_message, state: FSMContext):
\n    """Показать текущий шаг редактирования"""
\n    from aiogram.types import CallbackQuery, Message
\n    
\n    data = await state.get_data()
\n    step = data.get('edit_step', 0)
\n    product_id = data.get('edit_product_id')
\n    
\n    async with get_session() as session:
\n        product = await session.get(Product, product_id)
\n        if not product:
\n            if isinstance(callback_or_message, CallbackQuery):
\n                await callback_or_message.answer("❌ Товар не найден", show_alert=True)
\n            else:
\n                await callback_or_message.answer("❌ Товар не найден")
\n            await state.clear()
\n            return
\n        
\n                # Получаем название категории безопасно
\n        category_name = "неизвестно"
\n        if product.category_id:
\n            category = await session.get(Category, product.category_id)
\n            if category:
\n                category_name = category.name
\n        
\n        steps = [
\n            ("название", product.name, "name"),
\n            ("описание", product.description or "нет", "description"),
\n            ("цена", f"{product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}", "price"),
\n            ("остатки", f"{product.stock_grams}{'г' if product.unit_type == 'grams' else 'шт'}", "stock"),
\n            ("единицы", f"{'грамм' if product.unit_type == 'grams' else 'штук'} (шаг: {product.measurement_step})", "unit_type"),
\n            ("изображение", "есть" if product.image_url else "нет", "image"),
\n            ("категория", category_name, "category")
\n        ]
\n        
\n        if step >= len(steps):
\n            # Все шаги пройдены, сохраняем
\n            await save_product_changes(callback_or_message, state)
\n            return
\n        
\n        field_name, current_value, field_key = steps[step]
\n        
\n        message_text = (
\n            f"✏️ Редактирование товара: {product.name}\n\n"
\n            f"Шаг {step + 1} из {len(steps)}: {field_name}\n"
\n            f"Текущее значение: {current_value}\n\n"
\n            f"Изменить {field_name}? (да/нет):"
\n        )
\n        
\n        if isinstance(callback_or_message, CallbackQuery):
\n            await callback_or_message.message.edit_text(message_text)
\n        else:
\n            await callback_or_message.answer(message_text)
\n        
\n        # Устанавливаем соответствующее состояние
\n        state_name = f"waiting_edit_confirm_{field_key}"
\n        if hasattr(AdminStates, state_name):
\n            await state.set_state(getattr(AdminStates, state_name))
\n        else:
\n            # Если состояния нет, используем общее
\n            await state.set_state(AdminStates.waiting_edit_confirm_name)
\n
\n# Дубликат удален: @admin_router.message(AdminStates.waiting_edit_confirm_name)
\n# Дубликат удален: @admin_router.message(AdminStates.waiting_edit_confirm_name)
\nasync def process_edit_step_response(message: Message, state: FSMContext):
\n    """Обработка ответа на шаге редактирования"""
\n    response = message.text.strip().lower()
\n    data = await state.get_data()
\n    step = data.get('edit_step', 0)
\n
\n    # Определяем поле на основе шага
\n    field_mapping = {
\n        0: ("name", "Введите новое название:", AdminStates.waiting_edit_confirm_description),
\n        1: ("description", "Введите новое описание (или 'нет' для удаления):", AdminStates.waiting_edit_confirm_price),
\n        2: ("price", "Введите новую цену (например: 750/шт или 500/гр):", AdminStates.waiting_edit_confirm_stock),
\n        3: ("stock", "Введите новое количество:", AdminStates.waiting_edit_confirm_unit_type),
\n        4: ("unit_type", "Выберите единицы: 1 - граммы, 2 - штуки:", AdminStates.waiting_edit_confirm_image),
\n        5: ("image", "Загрузите новое изображение или отправьте 'пропустить':", AdminStates.waiting_edit_confirm_category),
\n        6: ("category", "Введите ID новой категории:", AdminStates.waiting_edit_final_save)
\n    }
\n
\n    if response in ['да', 'д', 'yes', 'y']:
\n        # Пользователь хочет изменить
\n        if step in field_mapping:
\n            field_key, prompt, next_state = field_mapping[step]
\n            await state.update_data(edit_current_field=field_key)
\n            await message.answer(prompt)
\n            # Переходим в состояние для ввода значения
\n            await state.set_state(next_state)
\n        else:
\n            await message.answer("❌ Ошибка шага")
\n            await state.clear()
\n
\n    elif response in ['нет', 'н', 'no', 'n']:
\n        # Пользователь не хочет менять
\n        await state.update_data(edit_step=step + 1)
\n        await show_edit_step(message, state)
\n    else:
\n        await message.answer("❌ Ответьте 'да' или 'нет':")
\n
\n# Универсальный обработчик ввода значений
\n@admin_router.message(AdminStates.waiting_edit_confirm_description)
\n@admin_router.message(AdminStates.waiting_edit_confirm_price)
\n@admin_router.message(AdminStates.waiting_edit_confirm_stock)
\n@admin_router.message(AdminStates.waiting_edit_confirm_unit_type)
\n@admin_router.message(AdminStates.waiting_edit_confirm_image)
\n@admin_router.message(AdminStates.waiting_edit_confirm_category)
\n@admin_router.message(AdminStates.waiting_edit_final_save)
\nasync def process_edit_field_input(message: Message, state: FSMContext):
\n    """Обработка ввода нового значения для любого поля"""
\n    data = await state.get_data()
\n    step = data.get('edit_step', 0)
\n    
\n    # Определяем поле на основе шага
\n    field_mapping = {
\n        0: "name",
\n        1: "description", 
\n        2: "price",
\n        3: "stock",
\n        4: "unit_type",
\n        5: "image",
\n        6: "category"
\n    }
\n    
\n    field_key = field_mapping.get(step)
\n    
\n    if not field_key:
\n        await message.answer("❌ Ошибка: невозможно определить поле для редактирования")
\n        await state.clear()
\n        return
\n    
\n    # Сохраняем изменение
\n    new_value = message.text.strip()
\n    changes = data.get('edit_changes', {})
\n    
\n    # Простая обработка в зависимости от поля
\n    if field_key == "description":
\n        if new_value.lower() == 'нет':
\n            new_value = ''
\n        changes[field_key] = new_value
\n    elif field_key == "price":
\n        # Обработка цены
\n        try:
\n            if '/шт' in new_value.lower():
\n                price_text = new_value.lower().replace('/шт', '').strip()
\n                changes['price'] = float(price_text)
\n                changes['unit_type'] = 'pieces'
\n                changes['measurement_step'] = 1
\n            elif '/гр' in new_value.lower():
\n                price_text = new_value.lower().replace('/гр', '').strip()
\n                changes['price'] = float(price_text)
\n                changes['unit_type'] = 'grams'
\n                changes['measurement_step'] = 100
\n            else:
\n                # По умолчанию граммы
\n                changes['price'] = float(new_value)
\n                changes['unit_type'] = 'grams'
\n                changes['measurement_step'] = 100
\n        except ValueError:
\n            await message.answer("❌ Неверный формат цены. Пример: 750/шт или 500/гр")
\n            return
\n    elif field_key == "stock":
\n        try:
\n            changes['stock_grams'] = int(new_value)
\n        except ValueError:
\n            await message.answer("❌ Введите целое число")
\n            return
\n    elif field_key == "unit_type":
\n        if new_value == '1':
\n            changes['unit_type'] = 'grams'
\n            changes['measurement_step'] = 100
\n        elif new_value == '2':
\n            changes['unit_type'] = 'pieces'
\n            changes['measurement_step'] = 1
\n        else:
\n            await message.answer("❌ Введите '1' или '2'")
\n            return
\n    elif field_key == "image":
\n        # Для изображения просто сохраняем URL или текст
\n        if new_value.lower() in ['пропустить', 'skip', 'без изображения']:
\n            changes['image_url'] = None
\n        else:
\n            # Здесь должна быть логика загрузки изображения
\n            # Пока просто сохраняем текст
\n            changes['image_url'] = new_value
\n    elif field_key == "category":
\n        try:
\n            changes['category_id'] = int(new_value)
\n        except ValueError:
\n            await message.answer("❌ Введите числовой ID категории")
\n            return
\n    else:
\n        # Для названия просто сохраняем
\n        changes[field_key] = new_value
\n    
\n    await state.update_data(edit_changes=changes, edit_step=step + 1)
\n    await show_edit_step(message, state)
\nasync def process_edit_price_response(message: Message, state: FSMContext):
\n    await process_edit_step_response(message, state)
\n
\n@admin_router.message(AdminStates.waiting_edit_confirm_stock)
\nasync def process_edit_stock_response(message: Message, state: FSMContext):
\n    await process_edit_step_response(message, state)
\n
\n@admin_router.message(AdminStates.waiting_edit_confirm_unit_type)
\nasync def process_edit_unit_response(message: Message, state: FSMContext):
\n    await process_edit_step_response(message, state)
\n
\n@admin_router.message(AdminStates.waiting_edit_confirm_image)
\nasync def process_edit_image_response(message: Message, state: FSMContext):
\n    await process_edit_step_response(message, state)
\n
\n@admin_router.message(AdminStates.waiting_edit_confirm_category)
\nasync def process_edit_category_response(message: Message, state: FSMContext):
\n    await process_edit_step_response(message, state)
\n
\n@admin_router.message(AdminStates.waiting_edit_final_save)
\nasync def process_edit_final_response(message: Message, state: FSMContext):
\n    await process_edit_step_response(message, state)
\n
\nasync def save_product_changes(callback_or_message, state: FSMContext):
\n    """Сохранение всех изменений товара"""
\n    from aiogram.types import CallbackQuery, Message
\n    
\n    data = await state.get_data()
\n    product_id = data.get('edit_product_id')
\n    category_id = data.get('edit_category_id')
\n    changes = data.get('edit_changes', {})
\n    
\n    if not changes:
\n        message_text = "⚠️ Ничего не изменено. Редактирование отменено."
\n        if isinstance(callback_or_message, CallbackQuery):
\n            await callback_or_message.message.edit_text(message_text)
\n        else:
\n            await callback_or_message.answer(message_text)
\n        await state.clear()
\n        return
\n    
\n    try:
\n        async with get_session() as session:
\n            product = await session.get(Product, product_id)
\n            if not product:
\n                message_text = "❌ Товар не найден"
\n                if isinstance(callback_or_message, CallbackQuery):
\n                    await callback_or_message.message.edit_text(message_text)
\n                else:
\n                    await callback_or_message.answer(message_text)
\n                await state.clear()
\n                return
\n            
\n            # Применяем изменения
\n            for field, value in changes.items():
\n                if hasattr(product, field):
\n                    setattr(product, field, value)
\n            
\n            await session.commit()
\n            
\n            # Показываем результат
\n            changes_list = "\n".join([f"• {k}: {v}" for k, v in changes.items()])
\n            message_text = f"✅ Товар успешно обновлен!\n\nИзменения:\n{changes_list}"
\n            
\n            if isinstance(callback_or_message, CallbackQuery):
\n                await callback_or_message.message.edit_text(message_text)
\n            else:
\n                await callback_or_message.answer(message_text)
\n            
\n            # Возвращаем к списку товаров
\n            await show_products_after_edit(callback_or_message, category_id)
\n            
\n    except Exception as e:
\n        logger.error(f"Ошибка сохранения товара: {e}")
\n        message_text = f"❌ Ошибка сохранения: {e}"
\n        if isinstance(callback_or_message, CallbackQuery):
\n            await callback_or_message.message.edit_text(message_text)
\n        else:
\n            await callback_or_message.answer(message_text)
\n    
\n    await state.clear()
\n
\nasync def show_products_after_edit(callback_or_message, category_id: int):
\n    """Показать список товаров после редактирования"""
\n    from aiogram.types import CallbackQuery, Message
\n    
\n    async with get_session() as session:
\n        category = await session.get(Category, category_id)
\n        if not category:
\n            message_text = "❌ Категория не найдена"
\n            if isinstance(callback_or_message, CallbackQuery):
\n                await callback_or_message.message.edit_text(message_text)
\n            else:
\n                await callback_or_message.answer(message_text)
\n            return
\n        
\n        stmt = select(Product).where(Product.category_id == category_id)
\n        result = await session.execute(stmt)
\n        products = result.scalars().all()
\n        
\n        products_list = [
\n            {
\n                "id": p.id,
\n                "name": p.name,
\n                "price": p.price,
\n                "stock_grams": p.stock_grams,
\n                "available": p.available,
\n                "unit_type": p.unit_type
\n            }
\n            for p in products
\n        ]
\n        
\n        from keyboards import admin_product_management_keyboard
\n        message_text = f"🛒 Товары категории: {category.name}\n\nКоличество товаров: {len(products_list)}"
\n        
\n        if isinstance(callback_or_message, CallbackQuery):
\n            await callback_or_message.message.edit_text(
\n                message_text,
\n                reply_markup=admin_product_management_keyboard(products_list, category_id)
\n            )
\n        else:
\n            await callback_or_message.answer(
\n                message_text,
\n                reply_markup=admin_product_management_keyboard(products_list, category_id)
\n            )
\n@admin_router.callback_query(F.data.startswith("admin_delete_product:"))
\n# Полное пошаговое редактирование товара
\n
\n# ========== ПОЛНОЕ ПОШАГОВОЕ РЕДАКТИРОВАНИЕ ТОВАРА ==========
\n
\n@admin_router.callback_query(F.data == "admin_back")
\nasync def admin_back(callback: CallbackQuery):
\n    """Назад в главное меню админки"""
\n    if not await is_admin(callback.from_user.id):
\n        await callback.answer("⛔ Нет доступа", show_alert=True)
\n        return
\n        # Начинаем пошаговое редактирование
\n        await state.set_state(AdminStates.waiting_edit_confirm_name)
\n        await callback.message.edit_text(
\n            f"✏️ Пошаговое редактирование товара\n\n"
\n            f"Товар: {product.name}\n\n"
\n            f"📝 Шаг 1/7: Название\n"
\n            f"Текущее название: {product.name}\n\n"
\n            f"Хотите изменить название товара? (Да/Нет):"
\n        )
\n        await callback.answer()
