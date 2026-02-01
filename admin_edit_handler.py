"""
Дополнительный обработчик для поэтапного редактирования товаров
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from database import get_session, Product, Category
from config import settings

logger = logging.getLogger(__name__)
edit_router = Router()

async def is_admin(user_id: int) -> bool:
    return user_id == settings.admin_id

# Новые состояния для поэтапного редактирования
class AdminEditProductStates(StatesGroup):
    waiting_confirm_name = State()
    waiting_confirm_description = State()
    waiting_confirm_price = State()
    waiting_confirm_stock = State()
    waiting_confirm_image = State()
    waiting_confirm_category = State()
    waiting_new_name = State()
    waiting_new_description = State()
    waiting_new_price = State()
    waiting_new_stock = State()
    waiting_new_image = State()
    waiting_new_category = State()

# Новый callback для полного редактирования товара
@edit_router.callback_query(F.data.startswith("admin_edit_product_full:"))
async def admin_edit_product_full_handler(callback: CallbackQuery, state: FSMContext):
    """Полное редактирование товара по клику (новый метод)"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])
    
    async with get_session() as session:
        # Получаем данные товара
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        
        # Получаем категорию товара
        category = await session.get(Category, product.category_id)
        category_name = category.name if category else "Неизвестно"
        
        # Сохраняем данные в состоянии
        await state.update_data(
            edit_product_id=product_id,
            edit_product_category_id=category_id,
            edit_product_current=product,
            edit_product_category_name=category_name
        )
        
        # Начинаем поэтапное редактирование - Шаг 1: Название
        await state.set_state(AdminEditProductStates.waiting_confirm_name)
        
        product_info = (
            f"🛒 Редактирование товара: {product.name}\n\n"
            f"Текущие данные:\n"
            f"1️⃣ Название: {product.name}\n"
            f"2️⃣ Описание: {product.description or 'Нет описания'}\n"
            f"3️⃣ Цена: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n"
            f"4️⃣ Остатки: {product.stock_grams} {'г' if product.unit_type == 'grams' else 'шт'}\n"
            f"5️⃣ Изображение: {'Есть' if product.image_url else 'Нет'}\n"
            f"6️⃣ Категория: {category_name}\n\n"
            f"Шаг 1/6: Хотите отредактировать НАЗВАНИЕ товара?\n"
            f"(да/нет)"
        )
        
        await callback.message.edit_text(product_info)
    
    await callback.answer()

# Обработка ответа на вопрос о редактировании названия
@edit_router.message(AdminEditProductStates.waiting_confirm_name)
async def process_edit_product_confirm_name(message: Message, state: FSMContext):
    """Обработка ответа о редактировании названия"""
    response = message.text.strip().lower()
    data = await state.get_data()
    
    if response in ['да', 'д', 'давай', 'yes', 'y', '1']:
        # Переходим к редактированию названия
        await state.set_state(AdminEditProductStates.waiting_new_name)
        await message.answer(
            f"✏️ Введите новое название товара:\n"
            f"(Текущее: {data['edit_product_current'].name})"
        )
    elif response in ['нет', 'н', 'no', 'n', '0', 'не', 'неа']:
        # Пропускаем редактирование названия, переходим к следующему шагу
        await state.set_state(AdminEditProductStates.waiting_confirm_description)
        product = data['edit_product_current']
        
        await message.answer(
            f"✅ Оставляем название: {product.name}\n\n"
            f"Шаг 2/6: Хотите отредактировать ОПИСАНИЕ товара?\n"
            f"Текущее: {product.description or 'Нет описания'}\n"
            f"(да/нет)"
        )
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'")
        return

# Обработка нового названия
@edit_router.message(AdminEditProductStates.waiting_new_name)
async def process_edit_product_new_name(message: Message, state: FSMContext):
    """Обработка нового названия товара"""
    new_name = message.text.strip()
    
    if len(new_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите снова:")
        return
    
    await state.update_data(edit_product_new_name=new_name)
    
    data = await state.get_data()
    product = data['edit_product_current']
    
    # Переходим к следующему шагу
    await state.set_state(AdminEditProductStates.waiting_confirm_description)
    
    await message.answer(
        f"✅ Новое название принято: {new_name}\n\n"
        f"Шаг 2/6: Хотите отредактировать ОПИСАНИЕ товара?\n"
        f"Текущее: {product.description or 'Нет описания'}\n"
        f"(да/нет)"
    )

# Обработка ответа на вопрос о редактировании описания
@edit_router.message(AdminEditProductStates.waiting_confirm_description)
async def process_edit_product_confirm_description(message: Message, state: FSMContext):
    """Обработка ответа о редактировании описания"""
    response = message.text.strip().lower()
    data = await state.get_data()
    product = data['edit_product_current']
    
    if response in ['да', 'д', 'давай', 'yes', 'y', '1']:
        await state.set_state(AdminEditProductStates.waiting_new_description)
        await message.answer(
            f"📝 Введите новое описание товара:\n"
            f"(Текущее: {product.description or 'Нет описания'})\n"
            f"Или отправьте 'нет' для удаления описания"
        )
    elif response in ['нет', 'н', 'no', 'n', '0', 'не', 'неа']:
        await state.set_state(AdminEditProductStates.waiting_confirm_price)
        
        await message.answer(
            f"✅ Оставляем описание\n\n"
            f"Шаг 3/6: Хотите отредактировать ЦЕНУ товара?\n"
            f"Текущая: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n"
            f"(да/нет)"
        )
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'")
        return

# Обработка нового описания
@edit_router.message(AdminEditProductStates.waiting_new_description)
async def process_edit_product_new_description(message: Message, state: FSMContext):
    """Обработка нового описания товара"""
    new_description = message.text.strip()
    
    if new_description.lower() == 'нет':
        new_description = ''
    
    await state.update_data(edit_product_new_description=new_description)
    
    data = await state.get_data()
    product = data['edit_product_current']
    
    # Переходим к следующему шагу
    await state.set_state(AdminEditProductStates.waiting_confirm_price)
    
    await message.answer(
        f"✅ Новое описание принято\n\n"
        f"Шаг 3/6: Хотите отредактировать ЦЕНУ товара?\n"
        f"Текущая: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n"
        f"(да/нет)"
    )

# Обработка ответа на вопрос о редактировании цены
@edit_router.message(AdminEditProductStates.waiting_confirm_price)
async def process_edit_product_confirm_price(message: Message, state: FSMContext):
    """Обработка ответа о редактировании цены"""
    response = message.text.strip().lower()
    data = await state.get_data()
    product = data['edit_product_current']
    
    if response in ['да', 'д', 'давай', 'yes', 'y', '1']:
        await state.set_state(AdminEditProductStates.waiting_new_price)
        await message.answer(
            f"💰 Введите новую цену с указанием единиц:\n"
            f"Формат: цена/шт или цена/гр\n"
            f"Пример: 750/шт или 500/гр\n\n"
            f"Текущая: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}"
        )
    elif response in ['нет', 'н', 'no', 'n', '0', 'не', 'неа']:
        await state.set_state(AdminEditProductStates.waiting_confirm_stock)
        
        await message.answer(
            f"✅ Оставляем цену\n\n"
            f"Шаг 4/6: Хотите отредактировать ОСТАТКИ товара?\n"
            f"Текущие: {product.stock_grams} {'г' if product.unit_type == 'grams' else 'шт'}\n"
            f"(да/нет)"
        )
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'")
        return

# Обработка новой цены
@edit_router.message(AdminEditProductStates.waiting_new_price)
async def process_edit_product_new_price(message: Message, state: FSMContext):
    """Обработка новой цены товара"""
    try:
        text = message.text.strip().lower()
        
        # Определяем единицы измерения (как при добавлении товара)
        if '/шт' in text:
            price_text = text.replace('/шт', '').strip()
            unit_type = 'pieces'
            measurement_step = 1
            price_label = 'RSD/шт'
        elif '/гр' in text:
            price_text = text.replace('/гр', '').strip()
            unit_type = 'grams'
            measurement_step = 100
            price_label = 'RSD/100г'
        else:
            # По умолчанию - граммы
            price_text = text
            unit_type = 'grams'
            measurement_step = 100
            price_label = 'RSD/100г'
        
        new_price = float(price_text)
        if new_price <= 0:
            await message.answer("❌ Цена должна быть больше 0. Введите снова:")
            return

        await state.update_data(
            edit_product_new_price=new_price,
            edit_product_new_unit_type=unit_type,
            edit_product_new_measurement_step=measurement_step
        )
        
        data = await state.get_data()
        product = data['edit_product_current']
        
        # Переходим к следующему шагу
        await state.set_state(AdminEditProductStates.waiting_confirm_stock)
        
        await message.answer(
            f"✅ Новая цена принята: {new_price} {price_label}\n\n"
            f"Шаг 4/6: Хотите отредактировать ОСТАТКИ товара?\n"
            f"Текущие: {product.stock_grams} {'г' if product.unit_type == 'grams' else 'шт'}\n"
            f"(да/нет)"
        )
    except ValueError:
        await message.answer("❌ Введите число в формате: цена/шт или цена/гр\n"
                           "Пример: 750/шт или 500/гр")

# Обработка ответа на вопрос о редактировании остатков
@edit_router.message(AdminEditProductStates.waiting_confirm_stock)
async def process_edit_product_confirm_stock(message: Message, state: FSMContext):
    """Обработка ответа о редактировании остатков"""
    response = message.text.strip().lower()
    data = await state.get_data()
    product = data['edit_product_current']
    
    if response in ['да', 'д', 'давай', 'yes', 'y', '1']:
        await state.set_state(AdminEditProductStates.waiting_new_stock)
        await message.answer(
            f"📦 Введите новое количество товара:\n"
            f"Только число\n"
            f"Текущее: {product.stock_grams} {'г' if product.unit_type == 'grams' else 'шт'}"
        )
    elif response in ['нет', 'н', 'no', 'n', '0', 'не', 'неа']:
        await state.set_state(AdminEditProductStates.waiting_confirm_image)
        
        image_status = 'Есть' if product.image_url else 'Нет'
        await message.answer(
            f"✅ Оставляем остатки\n\n"
            f"Шаг 5/6: Хотите отредактировать ИЗОБРАЖЕНИЕ товара?\n"
            f"Текущий статус: {image_status}\n"
            f"(да/нет)"
        )
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'")
        return

# Обработка новых остатков
@edit_router.message(AdminEditProductStates.waiting_new_stock)
async def process_edit_product_new_stock(message: Message, state: FSMContext):
    """Обработка новых остатков товара"""
    try:
        new_stock = int(message.text.strip())
        if new_stock < 0:
            await message.answer("❌ Количество не может быть отрицательным. Введите снова:")
            return

        await state.update_data(edit_product_new_stock=new_stock)
        
        data = await state.get_data()
        product = data['edit_product_current']
        
        # Переходим к следующему шагу
        await state.set_state(AdminEditProductStates.waiting_confirm_image)
        
        image_status = 'Есть' if product.image_url else 'Нет'
        await message.answer(
            f"✅ Новое количество принято: {new_stock}\n\n"
            f"Шаг 5/6: Хотите отредактировать ИЗОБРАЖЕНИЕ товара?\n"
            f"Текущий статус: {image_status}\n"
            f"(да/нет)"
        )
    except ValueError:
        await message.answer("❌ Введите число. Введите снова:")

# Обработка ответа на вопрос о редактировании изображения
@edit_router.message(AdminEditProductStates.waiting_confirm_image)
async def process_edit_product_confirm_image(message: Message, state: FSMContext):
    """Обработка ответа о редактировании изображения"""
    response = message.text.strip().lower()
    data = await state.get_data()
    product = data['edit_product_current']
    category_name = data.get('edit_product_category_name', 'Неизвестно')
    
    if response in ['да', 'д', 'давай', 'yes', 'y', '1']:
        await state.set_state(AdminEditProductStates.waiting_new_image)
        await message.answer(
            f"🖼️ Загрузите новое изображение товара.\n"
            f"Или отправьте 'пропустить' если хотите удалить текущее изображение"
        )
    elif response in ['нет', 'н', 'no', 'n', '0', 'не', 'неа']:
        await state.set_state(AdminEditProductStates.waiting_confirm_category)
        
        await message.answer(
            f"✅ Оставляем изображение\n\n"
            f"Шаг 6/6: Хотите отредактировать КАТЕГОРИЮ товара?\n"
            f"Текущая: {category_name}\n"
            f"(да/нет)"
        )
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'")
        return

# Обработка нового изображения
@edit_router.message(AdminEditProductStates.waiting_new_image)
async def process_edit_product_new_image(message: Message, state: FSMContext):
    """Обработка нового изображения товара"""
    new_image_url = None

    if message.text and message.text.strip().lower() in ['пропустить', 'skip', 'без изображения', 'удалить']:
        new_image_url = None
        await message.answer("✅ Изображение будет удалено")
    elif message.photo:
        # Используем file_id от телеграма
        new_image_url = message.photo[-1].file_id
        await message.answer(f"✅ Новое изображение получено")
    else:
        await message.answer("❌ Пожалуйста, загрузите изображение или отправьте 'пропустить'")
        return

    await state.update_data(edit_product_new_image=new_image_url)
    
    data = await state.get_data()
    category_name = data.get('edit_product_category_name', 'Неизвестно')
    
    # Переходим к следующему шагу
    await state.set_state(AdminEditProductStates.waiting_confirm_category)
    
    await message.answer(
        f"✅ Изображение обработано\n\n"
        f"Шаг 6/6: Хотите отредактировать КАТЕГОРИЮ товара?\n"
        f"Текущая: {category_name}\n"
        f"(да/нет)"
    )

# Обработка ответа на вопрос о редактировании категории
@edit_router.message(AdminEditProductStates.waiting_confirm_category)
async def process_edit_product_confirm_category(message: Message, state: FSMContext):
    """Обработка ответа о редактировании категории"""
    response = message.text.strip().lower()
    
    if response in ['да', 'д', 'давай', 'yes', 'y', '1']:
        # Получаем список категорий
        async with get_session() as session:
            stmt = select(Category).order_by(Category.name)
            result = await session.execute(stmt)
            categories = result.scalars().all()
        
        if not categories:
            await message.answer("❌ В базе данных нет категорий. Завершаем редактирование.")
            await save_product_changes(message, state)
            return
        
        categories_text = "\n".join([f"{cat.id}. {cat.name}" for cat in categories])
        
        await state.update_data(available_categories=categories)
        await state.set_state(AdminEditProductStates.waiting_new_category)
        
        await message.answer(
            f"📂 Выберите новую категорию:\n\n"
            f"Доступные категории:\n{categories_text}\n\n"
            f"Введите ID новой категории:"
        )
    elif response in ['нет', 'н', 'no', 'n', '0', 'не', 'неа']:
        await save_product_changes(message, state)
    else:
        await message.answer("❌ Пожалуйста, ответьте 'да' или 'нет'")
        return

# Обработка новой категории
@edit_router.message(AdminEditProductStates.waiting_new_category)
async def process_edit_product_new_category(message: Message, state: FSMContext):
    """Обработка новой категории товара"""
    try:
        new_category_id = int(message.text.strip())
        
        data = await state.get_data()
        categories = data.get('available_categories', [])
        
        # Проверяем существование категории
        category_exists = False
        category_name = ""
        for cat in categories:
            if cat.id == new_category_id:
                category_exists = True
                category_name = cat.name
                break
        
        if not category_exists:
            await message.answer(f"❌ Категория с ID {new_category_id} не найдена. Введите ID из списка:")
            return
        
        await state.update_data(edit_product_new_category=new_category_id)
        await save_product_changes(message, state, new_category_name=category_name)
        
    except ValueError:
        await message.answer("❌ Введите число (ID категории):")

# Функция сохранения всех изменений товара
async def save_product_changes(message: Message, state: FSMContext, new_category_name: str = None):
    """Сохранение всех изменений товара"""
    try:
        data = await state.get_data()
        product_id = data.get('edit_product_id')
        category_id = data.get('edit_product_category_id')
        product_current = data.get('edit_product_current')
        
        if not product_id:
            await message.answer("❌ Ошибка: ID товара не найден")
            await state.clear()
            return
        
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                await message.answer("❌ Товар не найден в базе данных")
                await state.clear()
                return
            
            # Собираем изменения
            changes = []
            
            # Название
            if 'edit_product_new_name' in data:
                old_name = product.name
                product.name = data['edit_product_new_name']
                changes.append(f"Название: {old_name} → {product.name}")
            
            # Описание
            if 'edit_product_new_description' in data:
                old_desc = product.description or "Нет"
                product.description = data['edit_product_new_description']
                new_desc = product.description or "Нет"
                changes.append(f"Описание: {old_desc} → {new_desc}")
            
            # Цена и единицы измерения
            if 'edit_product_new_price' in data:
                old_price = product.price
                product.price = data['edit_product_new_price']
                changes.append(f"Цена: {old_price} → {product.price}")
            
            if 'edit_product_new_unit_type' in data:
                old_unit = product.unit_type
                product.unit_type = data['edit_product_new_unit_type']
                changes.append(f"Единицы: {old_unit} → {product.unit_type}")
            
            if 'edit_product_new_measurement_step' in data:
                old_step = product.measurement_step
                product.measurement_step = data['edit_product_new_measurement_step']
                changes.append(f"Шаг измерения: {old_step} → {product.measurement_step}")
            
            # Остатки
            if 'edit_product_new_stock' in data:
                old_stock = product.stock_grams
                product.stock_grams = data['edit_product_new_stock']
                changes.append(f"Остатки: {old_stock} → {product.stock_grams}")
            
            # Изображение
            if 'edit_product_new_image' in data:
                old_image = "Есть" if product.image_url else "Нет"
                product.image_url = data['edit_product_new_image']
                new_image = "Есть" if product.image_url else "Нет"
                changes.append(f"Изображение: {old_image} → {new_image}")
            
            # Категория
            if 'edit_product_new_category' in data:
                old_category_id = product.category_id
                product.category_id = data['edit_product_new_category']
                changes.append(f"Категория: ID {old_category_id} → ID {product.category_id}")
            
            # Сохраняем изменения
            await session.commit()
            
            # Формируем сообщение с изменениями
            if changes:
                changes_text = "\n".join([f"• {change}" for change in changes])
                result_message = (
                    f"✅ Товар успешно обновлен!\n\n"
                    f"Изменения:\n{changes_text}\n\n"
                    f"Товар: {product.name}"
                )
            else:
                result_message = (
                    f"✅ Товар сохранен без изменений\n\n"
                    f"Товар: {product.name}"
                )
            
            await message.answer(result_message)
            
            # Возвращаем к списку товаров категории
            category = await session.get(Category, category_id)
            if category:
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
                await message.answer(
                    f"🛒 Товары категории: {category.name}\n\n"
                    f"Количество товаров: {len(products_list)}",
                    reply_markup=admin_product_management_keyboard(products_list, category_id)
                )
            else:
                # Если категория не найдена, возвращаем в главное меню админки
                from keyboards import admin_main_keyboard
                await message.answer(
                    "👑 Панель администратора\n\nВыберите действие:",
                    reply_markup=admin_main_keyboard()
                )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка сохранения товара: {e}")
        await message.answer(f"❌ Ошибка при сохранении товара: {str(e)}")
        await state.clear()
