"""
Все хендлеры бота - с исправленными кнопками +/- и улучшенным заказом
Версия с Reply Keyboard и Message Manager
"""
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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
    order_confirmation_keyboard,
    back_to_category_keyboard,
    admin_main_keyboard,
    admin_categories_keyboard,
    admin_products_keyboard,
    admin_product_management_keyboard
)
from reply_keyboards import get_main_reply_keyboard, get_catalog_reply_keyboard, get_cart_reply_keyboard, get_back_only_keyboard, remove_keyboard
from message_manager import message_manager
from services import cart_service, catalog_service, user_service
from database import get_session, Product, CartItem, User, Order, OrderItem
from sqlalchemy import select

logger = logging.getLogger(__name__)

# Создаем роутер
router = Router()

# ========== СОСТОЯНИЯ ДЛЯ ЗАКАЗА ==========

class OrderForm(StatesGroup):
    waiting_pet_name = State()
    waiting_telegram_login = State()
    checking_address = State()
    new_address = State()
    save_address_choice = State()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def safe_edit_message(callback: CallbackQuery, text: str, **kwargs):
    """Безопасное редактирование сообщения с обработкой ошибок"""
    try:
        await callback.message.edit_text(text, **kwargs)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Сообщение уже такое же - игнорируем
            logger.debug("Сообщение не изменилось, пропускаем")
        else:
            raise

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    try:
        # Создаем/получаем пользователя
        user = await cart_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )
        
        welcome_text = (
            "🐕 Добро пожаловать в Barkery Shop!\n\n"
            "Магазин натуральных собачьих лакомств 🦴\n\n"
            "Используйте кнопки ниже для навигации:"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.answer("❌ Ошибка запуска бота")

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = (
        "🐾 Помощь по боту Barkery Shop\n\n"
        "📦 Каталог - просмотр товаров по категориям\n"
        "🛒 Корзина - ваши выбранные товары\n"
        "👤 Профиль - ваши данные\n\n"
        "📱 Как сделать заказ:\n"
        "1. Выберите товары в каталоге\n"
        "2. Добавьте их в корзину\n"
        "3. Перейдите в корзину\n"
        "4. Оформите заказ\n\n"
        "💬 Поддержка: @support"
    )
    
    await message.answer(help_text)

# ========== ОБРАБОТЧИКИ REPLY KEYBOARD КНОПОК ==========

@router.message(F.text == "📦 Каталог")
async def handle_catalog_text(message: Message):
    """Обработка кнопки Каталог из Reply Keyboard"""
    try:
        # Получаем категории напрямую
        categories = await catalog_service.get_categories()
        
        if not categories:
            await message_manager.send_with_cleanup(
                bot=message.bot,
                chat_id=message.from_user.id,
                text="📦 Каталог\n\nКатегории пока не добавлены."
            )
            return
        
        # Создаем клавиатуру с категориями
        await message_manager.send_with_cleanup(
            bot=message.bot,
            chat_id=message.from_user.id,
            text="📦 Каталог\n\nВыберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа категорий: {e}")
        await message.answer("❌ Ошибка загрузки категорий")

@router.message(F.text == "🛒 Корзина")
async def handle_cart_text(message: Message):
    """Обработка кнопки Корзина из Reply Keyboard"""
    try:
        user = await cart_service.get_or_create_user(message.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await message_manager.send_with_cleanup(
                bot=message.bot,
                chat_id=message.from_user.id,
                text="🛒 Корзина пуста\n\nДобавьте товары из каталога!"
            )
            return
        
        # Формируем текст с списком товаров
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity_grams']}г - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        cart_text = (
            f"🛒 Ваша корзина\n\n"
            f"{items_text}\n\n"
            f"📦 Товаров: {cart_data['total_items']} шт.\n"
            f"💰 Итого: {cart_data['total_price']:.0f} RSD\n\n"
            f"Используйте кнопки ниже для управления корзиной:"
        )
        
        await message_manager.send_with_cleanup(
            bot=message.bot,
            chat_id=message.from_user.id,
            text=cart_text,
            reply_markup=get_cart_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа корзины: {e}")
        await message.answer("❌ Ошибка загрузки корзины")

@router.message(F.text == "👤 Профиль")
async def handle_profile_text(message: Message):
    """Обработка кнопки Профиль из Reply Keyboard"""
    try:
        user = await cart_service.get_or_create_user(message.from_user.id)
        
        # Получаем адреса пользователя
        addresses = await user_service.get_user_addresses(user.id)
        
        profile_text = (
            f"👤 Ваш профиль\n\n"
            f"🐕 Питомец: {user.full_name or 'Не указано'}\n"
            f"📱 Telegram: @{user.username or 'Не указан'}\n"
            f"🆔 ID: {user.id}\n"
            f"📅 Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}\n"
        )
        
        if addresses:
            profile_text += f"\n📍 Адреса доставки:\n"
            for addr in addresses[:3]:  # Показываем только первые 3 адреса
                default_marker = " ✅" if addr["is_default"] else ""
                profile_text += f"• {addr['address']}{default_marker}\n"
        
        await message_manager.send_with_cleanup(
            bot=message.bot,
            chat_id=message.from_user.id,
            text=profile_text,
            reply_markup=get_main_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа профиля: {e}")
        await message.answer("❌ Ошибка")

@router.message(F.text == "❓ Помощь")
async def handle_help_text(message: Message):
    """Обработка кнопки Помощь из Reply Keyboard"""
    help_text = (
        "🐾 Помощь по боту Barkery Shop\n\n"
        "📦 Каталог - просмотр товаров по категориям\n"
        "🛒 Корзина - ваши выбранные товары\n"
        "👤 Профиль - ваши данные\n\n"
        "📱 Как сделать заказ:\n"
        "1. Выберите товары в каталоге\n"
        "2. Добавьте их в корзину\n"
        "3. Перейдите в корзину\n"
        "4. Оформите заказ\n\n"
        "💬 Поддержка: @support"
    )
    
    await message_manager.send_with_cleanup(
        bot=message.bot,
        chat_id=message.from_user.id,
        text=help_text,
        reply_markup=get_main_reply_keyboard()
    )

@router.message(F.text == "⬅️ Назад")
async def handle_back_text(message: Message):
    """Обработка кнопки Назад из Reply Keyboard"""
    await message_manager.send_with_cleanup(
        bot=message.bot,
        chat_id=message.from_user.id,
        text="🐕 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_reply_keyboard()
    )

@router.message(F.text == "⬅️ Главная")
async def handle_home_text(message: Message):
    """Обработка кнопки Главная из Reply Keyboard"""
    await message_manager.send_with_cleanup(
        bot=message.bot,
        chat_id=message.from_user.id,
        text="🐕 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_reply_keyboard()
    )

# ========== CALLBACK ОБРАБОТЧИКИ (для Inline клавиатур) ==========

@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    """Главное меню (для callback)"""
    await message_manager.send_with_cleanup(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        text="🐕 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_reply_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery):
    """Показать категории (для callback)"""
    try:
        categories = await catalog_service.get_categories()
        
        if not categories:
            await message_manager.send_with_cleanup(
                bot=callback.bot,
                chat_id=callback.from_user.id,
                text="📦 Каталог\n\nКатегории пока не добавлены."
            )
            return
        
        await message_manager.send_with_cleanup(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            text="📦 Каталог\n\nВыберите категорию:",
            reply_markup=get_catalog_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа категорий: {e}")
        try:
            await callback.answer("❌ Ошибка загрузки категорий", show_alert=True)
        except Exception as answer_error:
            logger.warning(f"Не удалось отправить answer: {answer_error}")

@router.callback_query(F.data.startswith("category:"))
async def show_products(callback: CallbackQuery):
    """Показать товары категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        products = await catalog_service.get_products_by_category(category_id)
        
        if not products:
            await message_manager.send_with_cleanup(
                bot=callback.bot,
                chat_id=callback.from_user.id,
                text="📭 Товары\n\nВ этой категории пока нет товаров."
            )
            return
        
        await message_manager.send_with_cleanup(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            text="📦 Товары\n\nВыберите товар:",
            reply_markup=products_keyboard(products, category_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа товаров: {e}")
        try:
            await callback.answer("❌ Ошибка загрузки товаров", show_alert=True)
        except Exception as answer_error:
            logger.warning(f"Не удалось отправить answer: {answer_error}")

@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    """Показать карточку товара с изображением"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        category_id = int(parts[2])

        product = await catalog_service.get_product(product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        # Проверяем количество в корзине
        user = await cart_service.get_or_create_user(callback.from_user.id)
        async with get_session() as session:
            stmt = select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            current_qty = cart_item.quantity if cart_item else 0

        # Формируем текст
        description = product.get("description", "") or ""
        text = (
            f"🦴 {product['name']}\n\n"
            f"{description}\n\n"
            f"💰 Цена: {product['price']} RSD/100г\n"
            f"📦 В наличии: {product['stock_grams']}г\n"
            f"🛒 В корзине: {current_qty}г\n\n"
            "Выберите количество:"
        )
        
        keyboard = product_card_keyboard(product_id, category_id, current_qty)
        
        # Если есть изображение, отправляем фото с подписью
        if product.get('image_url'):
            try:
                await message_manager.send_photo_with_cleanup(
                    bot=callback.bot,
                    chat_id=callback.from_user.id,
                    photo=product['image_url'],
                    caption=text,
                    reply_markup=keyboard
                )
                await callback.answer()
            except Exception as photo_error:
                # Если не удалось отправить фото, используем обычное сообщение
                logger.warning(f"Не удалось отправить фото: {photo_error}")
                await message_manager.send_with_cleanup(
                    bot=callback.bot,
                    chat_id=callback.from_user.id,
                    text=text,
                    reply_markup=keyboard
                )
        else:
            # Без изображения - обычное сообщение
            await message_manager.send_with_cleanup(
                bot=callback.bot,
                chat_id=callback.from_user.id,
                text=text,
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Ошибка показа товара: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)

@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Назад к категориям"""
    await show_categories(callback)

@router.callback_query(F.data.startswith("back_to_products:"))
async def back_to_products(callback: CallbackQuery):
    """Назад к товарам категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        # Вызываем логику show_products напрямую
        products = await catalog_service.get_products_by_category(category_id)
        
        if not products:
            await message_manager.send_with_cleanup(
                bot=callback.bot,
                chat_id=callback.from_user.id,
                text="📭 Товары\n\nВ этой категории пока нет товаров."
            )
            await callback.answer()
            return
        
        await message_manager.send_with_cleanup(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            text="📦 Товары\n\nВыберите товар:",
            reply_markup=products_keyboard(products, category_id)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка возврата к товарам: {e}")
        try:
            await callback.answer("❌ Ошибка загрузки товаров", show_alert=True)
        except Exception as answer_error:
            logger.warning(f"Не удалось отправить answer: {answer_error}")

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    """Показать корзину - с списком товаров в тексте"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await message_manager.send_with_cleanup(
                bot=callback.bot,
                chat_id=callback.from_user.id,
                text="🛒 Корзина пуста\n\nДобавьте товары из каталога!"
            )
            return
        
        # Формируем текст с списком товаров
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity_grams']}г - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        cart_text = (
            f"🛒 Ваша корзина\n\n"
            f"{items_text}\n\n"
            f"📦 Товаров: {cart_data['total_items']} шт.\n"
            f"💰 Итого: {cart_data['total_price']:.0f} RSD\n\n"
            f"Используйте кнопки ниже для управления корзиной:"
        )
        
        await message_manager.send_with_cleanup(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            text=cart_text,
            reply_markup=get_cart_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа корзины: {e}")
        await callback.answer("❌ Ошибка загрузки корзины", show_alert=True)

@router.callback_query(F.data.startswith("qty_"))
async def handle_quantity(callback: CallbackQuery):
    """Обработка изменения количества с защитой от race condition"""
    try:
        logger.info(f"🎯 Обработка кнопки: {callback.data}")
        
        parts = callback.data.split(":")
        action = parts[0]  # qty_dec или qty_inc
        product_id = int(parts[1])
        category_id = int(parts[2])
        
        user = await cart_service.get_or_create_user(callback.from_user.id)
        
        # Определяем дельту
        delta = -100 if action == "qty_dec" else 100
        
        # Используем простую защиту от race condition
        async with get_session() as session:
            # Небольшая задержка для стабильности
            await asyncio.sleep(0.05)
            
            # Находим элемент корзины
            stmt = select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            
            if cart_item:
                new_quantity = cart_item.quantity + delta
                if new_quantity < 0:
                    new_quantity = 0
                
                # Проверяем наличие товара
                product = await session.get(Product, product_id)
                if product and new_quantity > product.stock_grams:
                    await callback.answer(
                        f"⚠️ Максимально доступно: {product.stock_grams}г",
                        show_alert=True
                    )
                    return
                
                cart_item.quantity = new_quantity
                await session.commit()
                
                # Обновляем клавиатуру
                keyboard = product_card_keyboard(product_id, category_id, new_quantity)
                await callback.message.edit_reply_markup(reply_markup=keyboard)
                
                qty_100g = new_quantity // 100
                await callback.answer(f"✅ Количество: {qty_100g} × 100г")
            else:
                # Если товара нет в корзине
                if delta > 0:
                    # Добавляем 100г
                    result = await cart_service.add_to_cart(user.id, product_id, 100)
                    if result["success"]:
                        keyboard = product_card_keyboard(product_id, category_id, 100)
                        await callback.message.edit_reply_markup(reply_markup=keyboard)
                        await callback.answer("✅ Добавлено: 100г")
                    else:
                        await callback.answer(result["error"], show_alert=True)
                else:
                    await callback.answer("❌ Товара нет в корзине")
        
    except Exception as e:
        logger.error(f"Ошибка изменения количества: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("cart_add:"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        quantity = int(parts[2])
        category_id = int(parts[3])
        
        if quantity <= 0:
            await callback.answer("⚠️ Количество должно быть больше 0", show_alert=True)
            return
        
        user = await cart_service.get_or_create_user(callback.from_user.id)
        result = await cart_service.add_to_cart(user.id, product_id, quantity)
        
        if result["success"]:
            # Получаем актуальные данные о товаре
            product = await catalog_service.get_product(product_id)
            
            # Обнуляем счетчик в карточке товара после добавления
            new_qty = 0  # Сбрасываем счетчик!
            
            # Формируем обновленный текст
            description = product.get("description", "") or ""
            text = (
                f"🦴 {product['name']}\n\n"
                f"{description}\n\n"
                f"💰 Цена: {product['price']} RSD/100г\n"
                f"📦 В наличии: {product['stock_grams']}г\n"
                f"🛒 В корзине: {quantity}г\n\n"  # Показываем сколько ТОЛЬКО ЧТО добавили
                "Выберите количество:"
            )
            
            # Обновляем И текст И клавиатуру (счетчик = 0)
            keyboard = product_card_keyboard(product_id, category_id, new_qty)
            try:
                await callback.message.edit_text(text, reply_markup=keyboard)
            except Exception as e:
                # Если не удалось обновить текст, обновляем хотя бы клавиатуру
                logger.warning(f"Не удалось обновить текст: {e}")
                await callback.message.edit_reply_markup(reply_markup=keyboard)
            
            await callback.answer(result["message"])
        else:
            await callback.answer(result["error"], show_alert=True)
            
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        await callback.answer("❌ Ошибка добавления", show_alert=True)

@router.callback_query(F.data.startswith("cart_remove:"))
async def remove_from_cart(callback: CallbackQuery):
    """Удалить товар из корзины"""
    try:
        product_id = int(callback.data.split(":")[1])
        
        user = await cart_service.get_or_create_user(callback.from_user.id)
        
        # Удаляем товар из корзины
        async with get_session() as session:
            stmt = select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            
            if cart_item:
                await session.delete(cart_item)
                await session.commit()
                
                # Получаем обновленные данные корзины
                cart_data = await cart_service.get_cart(user.id)
                
                if not cart_data["items"]:
                    # Корзина пуста
                    await message_manager.send_with_cleanup(
                        bot=callback.bot,
                        chat_id=callback.from_user.id,
                        text="✅ Товар удален\n\n🛒 Корзина пуста\n\nДобавьте товары из каталога!"
                    )
                else:
                    # Обновляем сообщение корзины
                    cart_text = (
                        f"✅ Товар удален\n\n"
                        f"🛒 Ваша корзина\n\n"
                        f"💰 Итого: {cart_data['total_price']:.0f} RSD\n"
                        f"📦 Товаров: {cart_data['total_items']} шт."
                    )
                    
                    await message_manager.send_with_cleanup(
                        bot=callback.bot,
                        chat_id=callback.from_user.id,
                        text=cart_text,
                        reply_markup=get_cart_reply_keyboard()
                    )
                
                await callback.answer("✅ Товар удален из корзины")
            else:
                await callback.answer("❌ Товар не найден в корзине", show_alert=True)
                
    except Exception as e:
        logger.error(f"Ошибка удаления товара: {e}")
        await callback.answer("❌ Ошибка удаления", show_alert=True)

@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        result = await cart_service.clear_cart(user.id)
        
        if result["success"]:
            await message_manager.send_with_cleanup(
                bot=callback.bot,
                chat_id=callback.from_user.id,
                text=f"✅ {result['message']}\n\nКорзина пуста."
            )
        await callback.answer(result["message"])
        
    except Exception as e:
        logger.error(f"Ошибка очистки корзины: {e}")
        await callback.answer("❌ Ошибка очистки", show_alert=True)

@router.callback_query(F.data == "cart_refresh")
async def refresh_cart(callback: CallbackQuery):
    """Обновить корзину"""
    await show_cart(callback)

# ========== ОБРАБОТКА ЗАКАЗА ==========
# (Оставляем оригинальные функции заказа без изменений)

@router.callback_query(F.data == "order_create")
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await callback.answer("🛒 Корзина пуста!", show_alert=True)
            return
        
        # Сохраняем данные о корзине
        await state.update_data(
            user_id=user.id,
            cart_items=cart_data["items"],
            total_amount=cart_data["total_price"]
        )
        
        # Проверяем, есть ли уже данные пользователя
        if user.full_name and user.username:
            # У пользователя уже есть данные - переходим к проверке адреса
            await state.update_data(
                pet_name=user.full_name,
                telegram_login=user.username
            )
            await state.set_state(OrderForm.checking_address)
            
            # Получаем адреса пользователя
            addresses = await user_service.get_user_addresses(user.id)
            if addresses:
                default_address = next((addr for addr in addresses if addr["is_default"]), addresses[0])
                
                await callback.message.answer(
                    f"🐕 Проверка адреса доставки\n\n"
                    f"👤 Питомец: {user.full_name}\n"
                    f"📱 Telegram: @{user.username or 'не указан'}\n\n"
                    f"📍 Текущий адрес доставки:\n{default_address['address']}\n\n"
                    "📋 Подтверждение адреса:\n"
                    "Если адрес доставки НЕ ИЗМЕНИЛСЯ, напишите 'нет'\n"
                    "Если адрес ИЗМЕНИЛСЯ, введите новый адрес доставки",
                    parse_mode="HTML"
                )
            else:
                # Нет адресов - запрашиваем новый
                await state.set_state(OrderForm.new_address)
                await callback.message.answer(
                    f"🐕 Введите адрес доставки\n\n"
                    f"👤 Питомец: {user.full_name}\n"
                    f"📱 Telegram: @{user.username or 'не указан'}\n\n"
                    "📍 Введите адрес доставки:\n"
                    "Улица, дом, квартира, район, город\n\n"
                    "Пример: ул. Кнез Михаилова 15, кв. 23, Стари-Град, Белград"
                )
        else:
            # У пользователя нет данных - запрашиваем все
            await state.set_state(OrderForm.waiting_pet_name)
            
            items_text = "\n".join([
                f"• {item['product_name']}: {item['quantity_grams']}г - {item['total_price']:.0f} RSD"
                for item in cart_data["items"]
            ])
            
            order_text = (
                "🛎️ Оформление заказа\n\n"
                f"Ваш заказ:\n{items_text}\n\n"
                f"Итого: {cart_data['total_price']:.0f} RSD\n\n"
                "Для оформления заказа нужна дополнительная информация.\n\n"
                "🐕 Шаг 1 из 3: Как зовут вашего питомца?"
            )
            
            await callback.message.answer(order_text)
        
    except Exception as e:
        logger.error(f"Ошибка начала заказа: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.message(OrderForm.waiting_pet_name)
async def process_pet_name(message: Message, state: FSMContext):
    """Обработка имени питомца"""
    pet_name = message.text.strip()
    
    if len(pet_name) < 2:
        await message.answer("❌ Слишком короткое имя. Введите имя питомца:")
        return
    
    await state.update_data(pet_name=pet_name)
    await state.set_state(OrderForm.waiting_telegram_login)
    
    await message.answer(
        f"✅ Имя питомец принято: {pet_name}\n\n"
        "📱 Шаг 2 из 3: Введите ваш Telegram login (без @):\n"
        "Например: ivanov_ivan"
    )

@router.message(OrderForm.waiting_telegram_login)
async def process_telegram_login(message: Message, state: FSMContext):
    """Обработка Telegram логина"""
    telegram_login = message.text.strip().replace("@", "")
    
    if len(telegram_login) < 3:
        await message.answer("❌ Слишком короткий login. Введите Telegram login:")
        return
    
    await state.update_data(telegram_login=telegram_login)
    await state.set_state(OrderForm.new_address)
    
    await message.answer(
        f"✅ Telegram login принят: @{telegram_login}\n\n"
        "📍 Шаг 3 из 3: Введите адрес доставки:\n"
        "Улица, дом, квартира, район, город\n\n"
        "Пример: ул. Кнез Михаилова 15, кв. 23, Стари-Град, Белград"
    )

@router.message(OrderForm.checking_address)
async def process_address_check(message: Message, state: FSMContext):
    """Проверка изменился ли адрес"""
    user_input = message.text.strip().lower()
    data = await state.get_data()
    
    if user_input == "нет":
        # Адрес не изменился - используем существующий
        addresses = await user_service.get_user_addresses(data["user_id"])
        default_address = next((addr for addr in addresses if addr["is_default"]), addresses[0])
        
        await state.update_data(address=default_address["address"])
        await confirm_order_data(message, state)
    else:
        # Введен новый адрес
        if len(user_input) < 10:
            await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
            return
        
        await state.update_data(new_address=user_input)
        await state.set_state(OrderForm.save_address_choice)
        
        await message.answer(
            f"📍 Новый адрес: {user_input}\n\n"
            "Хотите сохранить этот адрес как основной для будущих заказов?\n\n"
            "✅ Да - сохранить как основной адрес\n"
            "❌ Нет - использовать только для этого заказа"
        )

@router.message(OrderForm.new_address)
async def process_new_address(message: Message, state: FSMContext):
    """Обработка нового адреса (для новых пользователей)"""
    address = message.text.strip()
    
    if len(address) < 10:
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return
    
    data = await state.get_data()
    
    # Если это новый пользователь, сразу сохраняем адрес как основной
    if "pet_name" in data and "telegram_login" in data:
        # Сохраняем данные пользователя
        user_id = data["user_id"]
        await user_service.update_user_info(
            user_id, 
            pet_name=data["pet_name"], 
            telegram_login=data["telegram_login"]
        )
        
        # Сохраняем адрес как основной
        await user_service.add_user_address(user_id, address, is_default=True)
    
    await state.update_data(address=address)
    await confirm_order_data(message, state)

@router.message(OrderForm.save_address_choice)
async def process_save_address_choice(message: Message, state: FSMContext):
    """Обработка выбора сохранения адреса"""
    choice = message.text.strip().lower()
    data = await state.get_data()
    
    if choice in ["да", "yes", "✅", "+"]:
        # Сохраняем как основной адрес
        await user_service.add_user_address(
            data["user_id"], 
            data["new_address"], 
            is_default=True
        )
        await message.answer("✅ Адрес сохранен как основной")
    elif choice in ["нет", "no", "❌", "-"]:
        # Используем только для этого заказа
        await message.answer("📍 Адрес будет использован только для этого заказа")
    else:
        await message.answer("❌ Пожалуйста, ответьте 'Да' или 'Нет'")
        return
    
    await state.update_data(address=data["new_address"])
    await confirm_order_data(message, state)

async def confirm_order_data(message: Message, state: FSMContext):
    """Подтверждение данных заказа"""
    data = await state.get_data()
    
    # Формируем подтверждение
    items_text = "\n".join([
        f"• {item['product_name']}: {item['quantity_grams']}г - {item['total_price']:.0f} RSD"
        for item in data.get("cart_items", [])
    ])
    
    confirmation_text = (
        "✅ Подтверждение заказа\n\n"
        f"🐕 Питомец: {data.get('pet_name', 'Не указано')}\n"
        f"📱 Telegram: @{data.get('telegram_login', 'Не указан')}\n"
        f"📍 Адрес доставки: {data['address']}\n\n"
        f"📋 Состав заказа:\n{items_text}\n\n"
        f"💰 Итого к оплате: {data['total_amount']:.0f} RSD\n\n"
        "Проверьте данные и подтвердите заказ:"
    )
    
    await message.answer(
        confirmation_text,
        reply_markup=order_confirmation_keyboard()
    )

@router.callback_query(F.data == "order_confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа - ПРОСТАЯ ВЕРСИЯ"""
    try:
        data = await state.get_data()
        
        async with get_session() as session:
            # Создаем заказ
            import datetime
            
            order = Order(
                user_id=data["user_id"],
                customer_name=data.get("pet_name", "Не указано"),
                phone=f"@{data.get('telegram_login', 'Не указан')}",
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
                    quantity=item_data['quantity_grams']
                )
                session.add(order_item)
            
            await session.commit()
            
            # Очищаем корзину
            await cart_service.clear_cart(data["user_id"])
            
            # Уведомление админу
            try:
                from notifications import notify_admin

                # Формируем данные для уведомления
                order_data = {
                    "user_id": data["user_id"],
                    "pet_name": data.get("pet_name", "Не указано"),
                    "telegram_login": data.get("telegram_login", "Не указан"),
                    "address": data["address"],
                    "cart_items": data["cart_items"],
                    "total_amount": order.total_amount
                }

                # Отправляем уведомление через нашу новую функцию
                await notify_admin(callback.bot, order_data, order.id)

            except Exception as admin_error:
                logger.error(f"❌ Ошибка отправки уведомления админу: {admin_error}")

            # Очищаем состояние
            await state.clear()

            # УДАЛЯЕМ ВСЕ предыдущие сообщения в чате и отправляем новое
            try:
                # Удаляем сообщение с подтверждением заказа
                await callback.message.delete()
            except Exception as delete_error:
                logger.warning(f"Не удалось удалить сообщение: {delete_error}")

            # СОЗДАЕМ НОВОЕ ЧИСТОЕ СООБЩЕНИЕ с главным меню
            success_text = (
                "🎉 *Заказ успешно оформлен!*\n\n"
                f"📦 *Номер заказа:* #{order.id}\n"
                f"💰 *Сумма:* {order.total_amount:.0f} RSD\n\n"
                "📞 *Что дальше?*\n"
                "1. Мы свяжемся с вами для подтверждения заказа\n"
                "2. Подготовим ваши лакомства\n"
                "3. Доставим в течение 24 часов\n\n"
                "*Спасибо за покупку!* 🐶"
            )

            # Отправляем новое сообщение с главным меню
            await callback.message.answer(
                success_text,
                parse_mode="Markdown",
                reply_markup=get_main_reply_keyboard()
            )

            await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка подтверждения заказа: {e}")
        await callback.answer("❌ Ошибка создания заказа", show_alert=True)

@router.callback_query(F.data == "order_cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена заказа"""
    await state.clear()
    await message_manager.send_with_cleanup(
        bot=callback.bot,
        chat_id=callback.from_user.id,
        text="❌ Оформление заказа отменено\n\nВозвращаемся в корзину."
    )
    await show_cart(callback)

# ========== ПРОФИЛЬ ==========

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        
        # Получаем адреса пользователя
        addresses = await user_service.get_user_addresses(user.id)
        
        profile_text = (
            f"👤 Ваш профиль\n\n"
            f"🐕 Питомец: {user.full_name or 'Не указано'}\n"
            f"📱 Telegram: @{user.username or 'Не указан'}\n"
            f"🆔 ID: {user.id}\n"
            f"📅 Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}\n"
        )
        
        if addresses:
            profile_text += f"\n📍 Адреса доставки:\n"
            for addr in addresses[:3]:  # Показываем только первые 3 адреса
                default_marker = " ✅" if addr["is_default"] else ""
                profile_text += f"• {addr['address']}{default_marker}\n"
        
        await message_manager.send_with_cleanup(
            bot=callback.bot,
            chat_id=callback.from_user.id,
            text=profile_text,
            reply_markup=get_main_reply_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа профиля: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

# ========== ОБРАБОТКА НЕИЗВЕСТНЫХ КОЛБЭКОВ ==========

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Обработка неизвестных callback-запросов"""
    # Игнорируем админские колбэки - они должны обрабатываться админским роутером
    if callback.data.startswith("admin_"):
        logger.debug(f"Админский колбэк пропущен основным роутером: {callback.data}")
        return  # Пропускаем админские колбэки
    
    logger.warning(f"Неизвестный колбэк: {callback.data}")
    await callback.answer("⚠️ Эта кнопка больше не работает. Обновите меню.", show_alert=True)


@router.callback_query(F.data.startswith("cart_item:"))
@router.callback_query(F.data == "order_edit")
async def edit_order(callback: CallbackQuery):
    """Редактировать заказ"""
    await callback.answer("✏️ Для редактирования заказа вернитесь в корзину", show_alert=True)

@router.callback_query(F.data == "no_action")
async def handle_no_action(callback: CallbackQuery):
    """Кнопка которая ничего не делает"""
    await callback.answer()
