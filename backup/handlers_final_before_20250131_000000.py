"""
Barkery Bot - handlers.py
ОБНОВЛЕННАЯ ВЕРСИЯ с новой логикой оформления заказа
Обновлено: 2025-01-30
"""
import logging
import asyncio
import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from keyboards import (
    main_menu_keyboard,
    categories_keyboard,
    products_keyboard,
    product_card_keyboard,
    cart_keyboard,
    order_confirmation_keyboard
)
from services import cart_service, catalog_service
from database import get_session, Product, CartItem, User
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = Router()

# Храним предварительные количества для каждого пользователя и товара
temp_quantities = {}

# ========== СОСТОЯНИЯ ДЛЯ ЗАКАЗА ==========

class OrderForm(StatesGroup):
    """Новые состояния для оформления заказа"""
    waiting_pet_name = State()
    waiting_address = State()
    waiting_telegram_login = State()  # Только если не доступен
    confirm_address_change = State()  # Для повторных заказов

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_temp_quantity_key(user_id: str, product_id: int) -> str:
    """Ключ для хранения временного количества (используем telegram_id)"""
    return f"{user_id}_{product_id}"

def update_temp_quantity(user_id: str, product_id: int, delta: int) -> int:
    """Обновить временное количество с проверками"""
    key = get_temp_quantity_key(user_id, product_id)
    current = temp_quantities.get(key, 0)
    new_quantity = current + delta

    # Не может быть меньше 0
    if new_quantity < 0:
        new_quantity = 0

    temp_quantities[key] = new_quantity
    return new_quantity

def reset_temp_quantity(user_id: str, product_id: int):
    """Сбросить временное количество"""
    key = get_temp_quantity_key(user_id, product_id)
    temp_quantities[key] = 0

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С СООБЩЕНИЯМИ ==========

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None):
    """Безопасное редактирование сообщения (работает с фото и текстом)"""
    try:
        if callback.message.photo:
            # Если это фото, удаляем и отправляем текстовое сообщение
            await callback.message.delete()
            return await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=text,
                reply_markup=reply_markup
            )
        else:
            # Если это текст, редактируем
            return await callback.message.edit_text(
                text,
                reply_markup=reply_markup
            )
    except Exception as e:
        # Если не удалось, удаляем и отправляем заново
        logger.error(f"Ошибка безопасного редактирования: {e}")
        try:
            await callback.message.delete()
        except:
            pass

        return await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=reply_markup
        )

async def send_product_with_image(callback: CallbackQuery, product: dict, caption: str, keyboard):
    """Отправка товара с изображением или без"""
    try:
        # Удаляем предыдущее сообщение
        try:
            await callback.message.delete()
        except:
            pass

        if product.get('image_url'):
            # Отправляем фото с описанием
            return await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=product['image_url'],
                caption=caption,
                reply_markup=keyboard
            )
        else:
            # Отправляем текст
            return await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=caption,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Ошибка отправки товара: {e}")
        return await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=caption,
            reply_markup=keyboard
        )

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЯМИ ==========

async def check_user_info(telegram_id: str):
    """Проверить информацию о пользователе"""
    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            return {
                'exists': True,
                'user': user,
                'has_pet_name': bool(user.pet_name),
                'has_address': bool(user.address),
                'has_telegram_username': bool(user.telegram_username)
            }
        return {'exists': False}

async def update_user_info(telegram_id: str, data: dict):
    """Обновить информацию о пользователе"""
    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Создаем нового пользователя
            user = User(
                telegram_id=telegram_id,
                **{k: v for k, v in data.items() if k in ['pet_name', 'address', 'telegram_username', 'full_name']}
            )
            session.add(user)
        else:
            # Обновляем существующего пользователя
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
        
        await session.commit()
        await session.refresh(user)
        return user

async def update_user_last_order(telegram_id: str):
    """Обновить дату последнего заказа пользователя"""
    from sqlalchemy import update
    
    async with get_session() as session:
        stmt = update(User).where(User.telegram_id == telegram_id).values(
            last_order_date=datetime.datetime.now()
        )
        await session.execute(stmt)
        await session.commit()

# ========== КОМАНДЫ БОТА ==========

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    await message.answer(
        "🐶 Добро пожаловать в Barkery!\n\n"
        "Мы рады предложить натуральные лакомства для ваших питомцев.\n\n"
        "📦 Выбирайте товары по категориям:\n"
        "1. Сушеные лакомства\n"
        "2. Мясные снеки\n"
        "3. Фруктовые и овощные чипсы\n\n"
        "🛒 Добавляйте товары в корзину и оформляйте заказ 24/7!",
        reply_markup=main_menu_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработка команды /help"""
    await message.answer(
        "ℹ️ *Помощь по использованию бота*\n\n"
        "*Основные команды:*\n"
        "/start - Начало работы с ботом\n"
        "/help - Эта справка\n"
        "/menu - Показать главное меню\n"
        "/cart - Показать корзину\n\n"
        "*Как сделать заказ:*\n"
        "1. Выберите категорию товаров\n"
        "2. Выберите товар и добавьте его в корзину\n"
        "3. Перейдите в корзину и нажмите 'Оформить заказ'\n"
        "4. Заполните информацию о доставке\n\n"
        "*Форма оплаты:*\n"
        "💳 Оплата наличными при получении\n\n"
        "*Доставка:*\n"
        "🚚 Доставка по Белграду - 300 RSD\n"
        "📦 Самовывоз - бесплатно\n\n"
        "*Вопросы и поддержка:*\n"
        "📞 Свяжитесь с администратором через меню",
        parse_mode="Markdown"
    )

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    """Показать главное меню"""
    await message.answer(
        "🏠 *Главное меню*",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("cart"))
async def cmd_cart(message: Message):
    """Показать корзину"""
    try:
        user = await cart_service.get_or_create_user(message.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await message.answer("🛒 Ваша корзина пуста!")
            return
        
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        cart_text = (
            f"🛒 *Корзина*\n\n"
            f"{items_text}\n\n"
            f"*Итого:* {cart_data['total_price']:.0f} RSD"
        )
        
        await message.answer(
            cart_text,
            reply_markup=cart_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа корзины: {e}")
        await message.answer("❌ Ошибка загрузки корзины")

# ========== ГЛАВНОЕ МЕНЮ ==========

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery):
    """Показать главное меню"""
    await safe_edit_message(
        callback,
        "🏠 *Главное меню*",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery):
    """Показать категории товаров"""
    try:
        categories = await catalog_service.get_categories()
        await safe_edit_message(
            callback,
            "📦 *Категории товаров*",
            reply_markup=categories_keyboard(categories)
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки категорий: {e}")
        await callback.answer("❌ Ошибка загрузки категорий", show_alert=True)

@router.callback_query(F.data == "cart_view")
async def show_cart(callback: CallbackQuery):
    """Показать корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await safe_edit_message(
                callback,
                "🛒 Ваша корзина пуста!",
                reply_markup=main_menu_keyboard()
            )
            return
        
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        cart_text = (
            f"🛒 *Корзина*\n\n"
            f"{items_text}\n\n"
            f"*Итого:* {cart_data['total_price']:.0f} RSD"
        )
        
        await safe_edit_message(
            callback,
            cart_text,
            reply_markup=cart_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка показа корзины: {e}")
        await callback.answer("❌ Ошибка загрузки корзины", show_alert=True)

@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    """Показать информацию о поддержке"""
    await safe_edit_message(
        callback,
        "📞 *Поддержка и контакты*\n\n"
        "🕒 *Режим работы:* 24/7\n\n"
        "📱 *Telegram:* @barkery_support\n"
        "📧 *Email:* support@barkery.rs\n\n"
        "*Адрес самовывоза:*\n"
        "Белград, ул. Кнез Михаилова, 15\n\n"
        "*Время работы пункта выдачи:*\n"
        "Пн-Пт: 10:00-20:00\n"
        "Сб-Вс: 11:00-18:00",
        reply_markup=main_menu_keyboard()
    )

# ========== КАТАЛОГ ==========

@router.callback_query(F.data.startswith("category_"))
async def show_products(callback: CallbackQuery):
    """Показать товары в категории"""
    try:
        category_id = int(callback.data.split("_")[1])
        products = await catalog_service.get_products_by_category(category_id)
        
        if not products:
            await safe_edit_message(
                callback,
                "😔 В этой категории пока нет товаров",
                reply_markup=categories_keyboard(await catalog_service.get_categories())
            )
            return
        
        category_name = products[0]['category_name'] if products else "Категория"
        
        await safe_edit_message(
            callback,
            f"📦 *{category_name}*\n\n"
            "Выберите товар:",
            reply_markup=products_keyboard(products, category_id)
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки товаров: {e}")
        await callback.answer("❌ Ошибка загрузки товаров", show_alert=True)

@router.callback_query(F.data.startswith("product_"))
async def show_product_card(callback: CallbackQuery):
    """Показать карточку товара"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = await catalog_service.get_product(product_id)
        
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        
        # Получаем текущее количество из временного хранилища
        telegram_id = str(callback.from_user.id)
        current_quantity = temp_quantities.get(get_temp_quantity_key(telegram_id, product_id), 0)
        
        price_per_unit = f"{product['price']:.0f} RSD"
        if product['unit_type'] == 'grams':
            price_per_unit += " за 100г"
        else:
            price_per_unit += " за шт"
        
        caption = (
            f"*{product['name']}*\n\n"
            f"{product['description']}\n\n"
            f"💰 Цена: {price_per_unit}\n"
            f"📦 Наличие: {'✅ В наличии' if product['available'] else '❌ Нет в наличии'}\n"
        )
        
        await send_product_with_image(
            callback,
            product,
            caption,
            product_card_keyboard(product_id, current_quantity, product['unit_type'])
        )
    except Exception as e:
        logger.error(f"Ошибка загрузки товара: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)

@router.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = await catalog_service.get_product(product_id)
        
        if not product or not product['available']:
            await callback.answer("❌ Товар недоступен", show_alert=True)
            return
        
        # Получаем или создаем пользователя
        user = await cart_service.get_or_create_user(callback.from_user.id)
        
        # Определяем количество для добавления
        telegram_id = str(callback.from_user.id)
        if product['unit_type'] == 'grams':
            quantity_to_add = 100  # 100 грамм
        else:
            quantity_to_add = 1   # 1 штука
        
        # Добавляем в корзину
        result = await cart_service.add_to_cart(user.id, product_id, quantity_to_add)
        
        if result["success"]:
            # Обновляем временное количество
            new_quantity = update_temp_quantity(telegram_id, product_id, quantity_to_add)
            
            # Обновляем клавиатуру
            if callback.message.photo:
                await callback.message.edit_reply_markup(
                    reply_markup=product_card_keyboard(product_id, new_quantity, product['unit_type'])
                )
            else:
                await callback.message.edit_reply_markup(
                    reply_markup=product_card_keyboard(product_id, new_quantity, product['unit_type'])
                )
            
            await callback.answer(f"✅ {result['message']}")
        else:
            await callback.answer(f"❌ {result['message']}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        await callback.answer("❌ Ошибка добавления", show_alert=True)

@router.callback_query(F.data.startswith("remove_"))
async def remove_from_cart(callback: CallbackQuery):
    """Убрать товар из корзины"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = await catalog_service.get_product(product_id)
        
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        
        # Получаем пользователя
        user = await cart_service.get_or_create_user(callback.from_user.id)
        
        # Определяем количество для удаления
        telegram_id = str(callback.from_user.id)
        if product['unit_type'] == 'grams':
            quantity_to_remove = 100  # 100 грамм
        else:
            quantity_to_remove = 1   # 1 штука
        
        # Убираем из корзины
        result = await cart_service.remove_from_cart(user.id, product_id, quantity_to_remove)
        
        if result["success"]:
            # Обновляем временное количество
            new_quantity = update_temp_quantity(telegram_id, product_id, -quantity_to_remove)
            
            # Обновляем клавиатуру
            if callback.message.photo:
                await callback.message.edit_reply_markup(
                    reply_markup=product_card_keyboard(product_id, new_quantity, product['unit_type'])
                )
            else:
                await callback.message.edit_reply_markup(
                    reply_markup=product_card_keyboard(product_id, new_quantity, product['unit_type'])
                )
            
            await callback.answer(f"✅ {result['message']}")
        else:
            await callback.answer(f"❌ {result['message']}", show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка удаления из корзины: {e}")
        await callback.answer("❌ Ошибка удаления", show_alert=True)

# ========== КОРЗИНА ==========

@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        result = await cart_service.clear_cart(user.id)
        
        if result["success"]:
            # Очищаем временные количества пользователя
            telegram_id = str(callback.from_user.id)
            user_prefix = f"{telegram_id}_"
            keys_to_remove = [k for k in temp_quantities.keys() if k.startswith(user_prefix)]
            for key in keys_to_remove:
                del temp_quantities[key]
            
            await safe_edit_message(
                callback,
                f"✅ {result['message']}\n\nКорзина пуста.",
                reply_markup=main_menu_keyboard()
            )
        await callback.answer(result["message"])
        
    except Exception as e:
        logger.error(f"Ошибка очистки корзины: {e}")
        await callback.answer("❌ Ошибка очистки", show_alert=True)

# ========== ОБРАБОТКА ЗАКАЗА ==========

@router.callback_query(F.data == "order_create")
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа - НОВАЯ ВЕРСИЯ"""
    try:
        telegram_id = str(callback.from_user.id)
        user_info = await check_user_info(telegram_id)
        
        # Получаем информацию о корзине
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await callback.answer("🛒 Корзина пуста!", show_alert=True)
            return

        # Сохраняем данные о корзине
        await state.update_data(
            telegram_id=telegram_id,
            cart_items=cart_data["items"],
            total_amount=cart_data["total_price"],
            username=callback.from_user.username,
            full_name=callback.from_user.full_name
        )
        
        # ПРОВЕРКА 1: Если пользователь уже существует и у него есть вся информация
        if user_info['exists'] and user_info['has_pet_name'] and user_info['has_address'] and user_info['has_telegram_username']:
            # Пользователь уже есть в базе с полной информацией
            # Уточняем адрес доставки
            await state.update_data(
                pet_name=user_info['user'].pet_name,
                telegram_login=user_info['user'].telegram_username or callback.from_user.username or ""
            )
            
            items_text = "\n".join([
                f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
                for item in cart_data["items"]
            ])
            
            order_text = (
                "🛎️ Оформление заказа\n\n"
                f"Ваш заказ:\n{items_text}\n\n"
                f"Итого: {cart_data['total_price']:.0f} RSD\n\n"
                f"🐕 Питомец: {user_info['user'].pet_name}\n"
                f"📱 Telegram: @{user_info['user'].telegram_username or 'не указан'}\n\n"
                "📍 Адрес доставки остался прежним?\n"
                f"Текущий адрес: {user_info['user'].address}\n\n"
                "Если адрес остался прежним, введите \"нет\"\n"
                "Если адрес изменился, введите новый адрес:"
            )
            
            await state.set_state(OrderForm.confirm_address_change)
            await safe_edit_message(callback, order_text)
            return
        
        # ПРОВЕРКА 2: Если пользователь новый или информация неполная
        # Переходим к заполнению данных с начала
        await state.set_state(OrderForm.waiting_pet_name)
        
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        order_text = (
            "🛎️ Оформление заказа\n\n"
            f"Ваш заказ:\n{items_text}\n\n"
            f"Итого: {cart_data['total_price']:.0f} RSD\n\n"
            "Для оформления заказа нужна дополнительная информация.\n\n"
            "🐕 Шаг 1 из 3: Как зовут вашего питомца?"
        )
        
        await safe_edit_message(callback, order_text)
        
    except Exception as e:
        logger.error(f"Ошибка начала заказа: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.message(OrderForm.waiting_pet_name)
async def process_pet_name(message: Message, state: FSMContext):
    """Обработка имени питомца - Шаг 1"""
    pet_name = message.text.strip()
    
    if len(pet_name) < 2:
        try:
            await message.delete()
        except:
            pass
        
        await message.answer("❌ Слишком короткое имя. Введите имя питомца:")
        return
    
    await state.update_data(pet_name=pet_name)
    
    # Проверяем наличие username у пользователя Telegram
    data = await state.get_data()
    username = data.get('username') or message.from_user.username
    
    if username:
        # У пользователя есть @telegram_login, пропускаем шаг
        await state.update_data(telegram_login=username)
        await state.set_state(OrderForm.waiting_address)
        
        await message.answer(
            f"✅ Имя питомца принято: {pet_name}\n"
            f"✅ Telegram login определен: @{username}\n\n"
            "📍 Шаг 2 из 3: Введите адрес доставки:\n"
            "Улица, дом, квартира, район, город\n\n"
            "Пример: ул. Кнез Михаилова 15, кв. 23, Стари-Град, Белград"
        )
    else:
        # У пользователя скрыт @telegram_login, запрашиваем
        await state.set_state(OrderForm.waiting_telegram_login)
        
        await message.answer(
            f"✅ Имя питомца принято: {pet_name}\n\n"
            "📱 Шаг 2 из 3: Введите ваш Telegram login (без @):\n"
            "Например: ivanov_ivan"
        )

@router.message(OrderForm.waiting_telegram_login)
async def process_telegram_login(message: Message, state: FSMContext):
    """Обработка Telegram логина - Шаг 2 (если username скрыт)"""
    telegram_login = message.text.strip().replace("@", "")
    
    if len(telegram_login) < 3:
        try:
            await message.delete()
        except:
            pass
        
        await message.answer("❌ Слишком короткий login. Введите Telegram login:")
        return
    
    await state.update_data(telegram_login=telegram_login)
    await state.set_state(OrderForm.waiting_address)
    
    await message.answer(
        f"✅ Telegram login принят: @{telegram_login}\n\n"
        "📍 Шаг 3 из 3: Введите адрес доставки:\n"
        "Улица, дом, квартира, район, город\n\n"
        "Пример: ул. Кнез Михаилова 15, кв. 23, Стари-Град, Белград"
    )

@router.message(OrderForm.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса доставки - Шаг 3"""
    address = message.text.strip()
    
    if len(address) < 10:
        try:
            await message.delete()
        except:
            pass
        
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return
    
    data = await state.get_data()
    
    # Сохраняем информацию о пользователе в БД
    user_data = {
        'pet_name': data.get('pet_name'),
        'address': address,
        'telegram_username': data.get('telegram_login'),
        'full_name': data.get('full_name', '')
    }
    
    user = await update_user_info(data['telegram_id'], user_data)
    
    # Показываем подтверждение заказа
    await show_order_confirmation(message, data, address, user)

@router.message(OrderForm.confirm_address_change)
async def process_address_change(message: Message, state: FSMContext):
    """Обработка изменения адреса для существующего пользователя"""
    user_input = message.text.strip().lower()
    
    data = await state.get_data()
    
    if user_input == "нет" or user_input == "нет." or user_input == "no":
        # Адрес не изменился, используем старый
        user_info = await check_user_info(data['telegram_id'])
        address = user_info['user'].address
        
        # Обновляем дату последнего заказа
        await update_user_last_order(data['telegram_id'])
        
        await show_order_confirmation(message, data, address, user_info['user'])
    else:
        # Адрес изменился, сохраняем новый
        if len(user_input) < 10:
            try:
                await message.delete()
            except:
                pass
            
            await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
            return
        
        # Обновляем адрес в БД
        from sqlalchemy import update
        
        async with get_session() as session:
            stmt = update(User).where(User.telegram_id == data['telegram_id']).values(
                address=user_input,
                last_order_date=datetime.datetime.now()
            )
            await session.execute(stmt)
            await session.commit()
        
        await show_order_confirmation(message, data, user_input)

async def show_order_confirmation(message: Message, data: dict, address: str, user=None):
    """Показать подтверждение заказа"""
    items_text = "\n".join([
        f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
        for item in data["cart_items"]
    ])
    
    confirmation_text = (
        "✅ Подтверждение заказа\n\n"
        f"🐕 Питомец: {data.get('pet_name', 'не указано')}\n"
        f"📱 Telegram: @{data.get('telegram_login', 'не указан')}\n"
        f"📍 Адрес доставки: {address}\n\n"
        f"📋 Состав заказа:\n{items_text}\n\n"
        f"💰 Итого к оплате: {data['total_amount']:.0f} RSD\n\n"
        "Подтвердите заказ:"
    )
    
    # Сохраняем адрес в состоянии
    from aiogram.fsm.context import FSMContext
    state = FSMContext(message.bot, message.chat.id, message.from_user.id)
    await state.update_data(address=address)
    
    await message.answer(
        confirmation_text,
        reply_markup=order_confirmation_keyboard()
    )

@router.callback_query(F.data == "order_confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    try:
        data = await state.get_data()

        async with get_session() as session:
            # Создаем заказ
            from database import Order, OrderItem
            
            order = Order(
                user_id=data.get("user_id"),  # Оставляем для обратной совместимости
                customer_name=data.get("pet_name", "Не указано"),
                phone=f"@{data.get('telegram_login', 'не указан')}",
                address=data['address'],
                total_amount=data['total_amount'],
                status="pending",
                created_at=datetime.datetime.now()
            )

            session.add(order)
            await session.commit()
            await session.refresh(order)

            # Создаем элементы заказа
            for item_data in data['cart_items']:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data['product_id'],
                    product_name=item_data['product_name'],
                    price_per_100g=item_data['price_per_100g'],
                    quantity=item_data['quantity']
                )
                session.add(order_item)

            await session.commit()

            # Очищаем корзину
            user = await cart_service.get_or_create_user(callback.from_user.id)
            await cart_service.clear_cart(user.id)

            # Очищаем временные количества пользователя
            telegram_id = str(callback.from_user.id)
            user_prefix = f"{telegram_id}_"
            keys_to_remove = [k for k in temp_quantities.keys() if k.startswith(user_prefix)]
            for key in keys_to_remove:
                del temp_quantities[key]

            # Уведомление админу
            try:
                from notifications import notify_admin
                await notify_admin(callback.bot, data, order.id)
            except Exception as admin_error:
                logger.error(f"❌ Ошибка отправки уведомления админу: {admin_error}")

            # Очищаем состояние
            await state.clear()

            # Показываем успех
            success_text = (
                "🎉 *Заказ успешно оформлен!*\n\n"
                f"📦 *Номер заказа:* #{order.id}\n"
                f"💰 *Сумма:* {order.total_amount:.0f} RSD\n\n"
                "📞 *Что дальше?*\n"
                "1. Мы свяжемся с вами для подтверждения заказа\n"
                "2. Подготовим ваши лакомства\n"
                "3. Согласуем условия самовывоза или доставки\n\n"
                "*Спасибо за покупку!* 🐶"
            )

            await safe_edit_message(
                callback,
                success_text,
                reply_markup=main_menu_keyboard()
            )

            await callback.answer()
            
    except Exception as e:
        logger.error(f"Ошибка подтверждения заказа: {e}")
        await callback.answer("❌ Ошибка оформления заказа", show_alert=True)

@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()
    await safe_edit_message(
        callback,
        "❌ Оформление заказа отменено",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()
