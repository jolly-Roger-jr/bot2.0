# handlers_smi.py
"""
Barkery Bot - Single Message Interface версия
Все взаимодействия в одном сообщении
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Импортируем наши менеджеры
from message_manager import message_manager
from state_manager import state_manager, NavigationState

# Импортируем клавиатуры SMI
from keyboards_smi import (
    main_menu_keyboard,
    categories_keyboard_smi,
    products_keyboard_smi,
    product_card_keyboard_smi,
    cart_keyboard_smi,
    order_form_keyboard
)

from services import cart_service, catalog_service, user_service
from database import get_session, CartItem
from sqlalchemy import select

logger = logging.getLogger(__name__)
router_smi = Router()

# Временное хранилище для предварительных количеств
temp_quantities = {}


# ========== СОСТОЯНИЯ ДЛЯ ЗАКАЗА ==========

class OrderFormSMI(StatesGroup):
    waiting_pet_name = State()
    waiting_address = State()
    waiting_telegram_login = State()
    waiting_confirmation = State()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_temp_quantity_key(user_id: int, product_id: int) -> str:
    """Ключ для временного количества"""
    return f"{user_id}_{product_id}"


def format_product_card(product: dict, current_in_cart: int = 0) -> str:
    """Форматировать карточку товара"""
    unit_type = product.get('unit_type', 'grams')

    if unit_type == 'grams':
        price_text = f"💰 Цена: {product['price']} RSD/100г"
        stock_text = f"📦 В наличии: {product['stock_grams']}г"
        cart_text = f"🛒 В корзине: {current_in_cart}г" if current_in_cart > 0 else ""
    else:
        price_text = f"💰 Цена: {product['price']} RSD/шт"
        stock_text = f"📦 В наличии: {product['stock_grams']}шт"
        cart_text = f"🛒 В корзине: {current_in_cart}шт" if current_in_cart > 0 else ""

    description = product.get('description', '')

    card_text = (
        f"🦴 <b>{product['name']}</b>\n\n"
    )

    if description:
        card_text += f"{description}\n\n"

    card_text += f"{price_text}\n"
    card_text += f"{stock_text}\n"

    if cart_text:
        card_text += f"{cart_text}\n"

    card_text += "\nВыберите количество:"

    return card_text


def format_cart_content(cart_data: dict) -> str:
    """Форматировать содержимое корзины"""
    if not cart_data["items"]:
        return "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога!"

    items_text = "\n".join([
        f"• {item['product_name']}: "
        f"{item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - "
        f"{item['total_price']:.0f} RSD"
        for item in cart_data["items"]
    ])

    return (
        f"🛒 <b>Ваша корзина</b>\n\n"
        f"{items_text}\n\n"
        f"📦 Товаров: {cart_data['total_items']} шт.\n"
        f"💰 Итого: {cart_data['total_price']:.0f} RSD"
    )


# ========== ОСНОВНЫЕ ОБРАБОТЧИКИ ==========

@router_smi.message(Command("start"))
async def smi_start(message: Message, state: FSMContext):
    """Начало работы - создаём единственное сообщение"""
    try:
        # Создаем/получаем пользователя
        user = await cart_service.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name
        )

        # Очищаем состояние
        await state.clear()

        # Создаём главное сообщение
        await message_manager.update_message(
            user_id=message.from_user.id,
            message_or_callback=message,
            text=(
                "🐕 <b>Добро пожаловать в Barkery Shop!</b>\n\n"
                "Магазин натуральных собачьих лакомств 🦴\n\n"
                "Используйте кнопки ниже для навигации:"
            ),
            keyboard=main_menu_keyboard()
        )

        # Сохраняем состояние
        await state_manager.save_current_state(
            user_id=message.from_user.id,
            screen="main_menu",
            fsm_context=state
        )

    except Exception as e:
        logger.error(f"Ошибка в smi_start: {e}")


# ========== ГЛАВНОЕ МЕНЮ ==========

@router_smi.callback_query(F.data == "smi_main")
async def smi_main_menu(callback: CallbackQuery, state: FSMContext):
    """Главное меню"""
    try:
        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=(
                "🐕 <b>Главное меню</b>\n\n"
                "Выберите действие:"
            ),
            keyboard=main_menu_keyboard()
        )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="main_menu",
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_main_menu: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# ========== КАТАЛОГ ==========

@router_smi.callback_query(F.data == "smi_catalog")
async def smi_show_categories(callback: CallbackQuery, state: FSMContext):
    """Показать категории"""
    try:
        categories = await catalog_service.get_categories()

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text="📦 <b>Каталог</b>\n\nВыберите категорию:",
            keyboard=categories_keyboard_smi(categories)
        )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="categories",
            data={"categories": categories},
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_show_categories: {e}")
        await callback.answer("❌ Ошибка загрузки категорий", show_alert=True)


@router_smi.callback_query(F.data.startswith("smi_category:"))
async def smi_show_products(callback: CallbackQuery, state: FSMContext):
    """Показать товары категории"""
    try:
        category_id = int(callback.data.split(":")[1])

        # Определяем тип категории
        if category_id == 999:
            # Гипоаллергенные товары
            products = await catalog_service.get_hypoallergenic_products()
            category_name = "🥕🐟 Гипоаллергенные 🐏🎃"
        else:
            # Обычные товары
            products = await catalog_service.get_products_by_category(category_id)
            category_name = f"Категория {category_id}"

        if not products:
            await message_manager.safe_edit_message(
                user_id=callback.from_user.id,
                message=callback.message,
                text=f"📭 <b>Товары категории: {category_name}</b>\n\nПока нет доступных товаров.",
                keyboard=categories_keyboard_smi([])
            )
            return

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=f"📦 <b>Товары категории: {category_name}</b>\n\nВыберите товар:",
            keyboard=products_keyboard_smi(products, category_id)
        )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="products_list",
            data={"category_id": category_id, "category_name": category_name},
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_show_products: {e}")
        await callback.answer("❌ Ошибка загрузки товаров", show_alert=True)


@router_smi.callback_query(F.data.startswith("smi_back_products:"))
async def smi_back_to_products(callback: CallbackQuery, state: FSMContext):
    """Назад к товарам категории"""
    try:
        category_id = int(callback.data.split(":")[1])

        # Получаем товары
        products = await catalog_service.get_products_by_category(category_id)

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=f"📦 <b>Товары категории</b>\n\nВыберите товар:",
            keyboard=products_keyboard_smi(products, category_id)
        )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="products_list",
            data={"category_id": category_id},
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_back_to_products: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# ========== КАРТОЧКА ТОВАРА ==========

@router_smi.callback_query(F.data.startswith("smi_product:"))
async def smi_show_product(callback: CallbackQuery, state: FSMContext):
    """Показать карточку товара"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        category_id = int(parts[2])

        # Получаем товар
        product = await catalog_service.get_product(product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        # Получаем количество в корзине
        user = await cart_service.get_or_create_user(callback.from_user.id)
        async with get_session() as session:
            stmt = select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            current_in_cart = cart_item.quantity if cart_item else 0

        # Формируем текст
        card_text = format_product_card(product, current_in_cart)

        # Получаем временное количество
        temp_key = get_temp_quantity_key(callback.from_user.id, product_id)
        temp_qty = temp_quantities.get(temp_key, 0)

        # Клавиатура
        keyboard = product_card_keyboard_smi(
            product_id,
            category_id,
            temp_qty,
            product.get("unit_type", "grams"),
            product.get("measurement_step", 100)
        )

        # Обновляем сообщение
        if product.get('image_url'):
            # Удаляем старое и создаём новое с фото
            await message_manager.update_message(
                user_id=callback.from_user.id,
                message_or_callback=callback.message,
                text=card_text,
                keyboard=keyboard,
                photo=product['image_url']
            )
        else:
            await message_manager.safe_edit_message(
                user_id=callback.from_user.id,
                message=callback.message,
                text=card_text,
                keyboard=keyboard
            )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="product_view",
            data={
                "product_id": product_id,
                "category_id": category_id,
                "product_name": product['name']
            },
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_show_product: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)


# ========== УПРАВЛЕНИЕ КОЛИЧЕСТВОМ ==========

@router_smi.callback_query(F.data.startswith("smi_qty_"))
async def smi_handle_quantity(callback: CallbackQuery, state: FSMContext):
    """Обработка изменения количества"""
    try:
        parts = callback.data.split(":")
        action = parts[0]

        if action == "smi_qty_info":
            await callback.answer("📊 Изменение количества")
            return

        product_id = int(parts[1])
        category_id = int(parts[2])

        # Получаем товар
        product = await catalog_service.get_product(product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        user = await cart_service.get_or_create_user(callback.from_user.id)

        # Получаем текущее количество в корзине
        async with get_session() as session:
            stmt = select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            current_in_cart = cart_item.quantity if cart_item else 0

        # Определяем дельту
        measurement_step = product.get('measurement_step', 100)
        delta = -measurement_step if "dec" in action else measurement_step

        # Обновляем временное количество
        temp_key = get_temp_quantity_key(callback.from_user.id, product_id)
        current_temp = temp_quantities.get(temp_key, 0)
        new_temp = current_temp + delta

        # Проверки
        if new_temp < 0:
            new_temp = 0

        # Проверяем общее количество
        total_qty = current_in_cart + new_temp
        if total_qty > product['stock_grams']:
            max_can_add = product['stock_grams'] - current_in_cart
            new_temp = max_can_add
            if max_can_add <= 0:
                await callback.answer("❌ Невозможно добавить больше", show_alert=True)
                return

        # Сохраняем
        temp_quantities[temp_key] = new_temp

        # Обновляем отображение
        card_text = format_product_card(product, current_in_cart)

        keyboard = product_card_keyboard_smi(
            product_id,
            category_id,
            new_temp,
            product.get("unit_type", "grams"),
            product.get("measurement_step", 100)
        )

        if callback.message.photo:
            await callback.message.edit_caption(
                caption=card_text,
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                text=card_text,
                reply_markup=keyboard
            )

        unit_symbol = "г" if product.get("unit_type", "grams") == "grams" else "шт"
        await callback.answer(f"Количество: {new_temp}{unit_symbol}")

    except Exception as e:
        logger.error(f"Ошибка в smi_handle_quantity: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router_smi.callback_query(F.data.startswith("smi_cart_add:"))
async def smi_add_to_cart(callback: CallbackQuery, state: FSMContext):
    """Добавить в корзину"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        quantity = int(parts[2])
        category_id = int(parts[3])

        if quantity <= 0:
            await callback.answer("⚠️ Сначала выберите количество", show_alert=True)
            return

        user = await cart_service.get_or_create_user(callback.from_user.id)
        result = await cart_service.add_to_cart(user.id, product_id, quantity)

        if result["success"]:
            # Сбрасываем временное количество
            temp_key = get_temp_quantity_key(callback.from_user.id, product_id)
            if temp_key in temp_quantities:
                del temp_quantities[temp_key]

            # Обновляем отображение
            product = await catalog_service.get_product(product_id)

            # Получаем новое количество в корзине
            async with get_session() as session:
                stmt = select(CartItem).where(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id
                )
                result2 = await session.execute(stmt)
                cart_item = result2.scalar_one_or_none()
                current_in_cart = cart_item.quantity if cart_item else 0

            card_text = format_product_card(product, current_in_cart)

            keyboard = product_card_keyboard_smi(
                product_id,
                category_id,
                0,  # Сбрасываем временное количество
                product.get("unit_type", "grams"),
                product.get("measurement_step", 100)
            )

            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=card_text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text=card_text,
                    reply_markup=keyboard
                )

            unit_symbol = "г" if product.get("unit_type", "grams") == "grams" else "шт"
            await callback.answer(f"✅ Добавлено: {quantity}{unit_symbol}")
        else:
            await callback.answer(result["error"], show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в smi_add_to_cart: {e}")
        await callback.answer("❌ Ошибка добавления", show_alert=True)


# ========== КОРЗИНА ==========

@router_smi.callback_query(F.data == "smi_cart")
async def smi_show_cart(callback: CallbackQuery, state: FSMContext):
    """Показать корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)

        cart_text = format_cart_content(cart_data)

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=cart_text,
            keyboard=cart_keyboard_smi(cart_data["total_items"], cart_data["total_price"])
        )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="cart_view",
            data={"cart_data": cart_data},
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_show_cart: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router_smi.callback_query(F.data == "smi_cart_clear")
async def smi_clear_cart(callback: CallbackQuery, state: FSMContext):
    """Очистить корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        result = await cart_service.clear_cart(user.id)

        if result["success"]:
            # Очищаем временные количества
            user_prefix = f"{callback.from_user.id}_"
            keys_to_remove = [k for k in temp_quantities.keys() if k.startswith(user_prefix)]
            for key in keys_to_remove:
                temp_quantities.pop(key, None)

            # Возвращаем в главное меню
            await message_manager.safe_edit_message(
                user_id=callback.from_user.id,
                message=callback.message,
                text=(
                    "🐕 <b>Главное меню</b>\n\n"
                    "✅ Корзина очищена\n\n"
                    "Выберите действие:"
                ),
                keyboard=main_menu_keyboard()
            )

            await state_manager.save_current_state(
                user_id=callback.from_user.id,
                screen="main_menu",
                fsm_context=state
            )

            await callback.answer("✅ Корзина очищена")
        else:
            await callback.answer(f"❌ {result.get('error')}", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в smi_clear_cart: {e}")
        await callback.answer("❌ Ошибка очистки", show_alert=True)


# ========== ЗАКАЗ ==========

@router_smi.callback_query(F.data == "smi_order_start")
async def smi_start_order(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)

        if not cart_data["items"]:
            await callback.answer("🛒 Корзина пуста!", show_alert=True)
            return

        # Переходим в состояние оформления
        await state.set_state(OrderFormSMI.waiting_pet_name)

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=(
                "🛎️ <b>Оформление заказа</b>\n\n"
                "Шаг 1 из 3\n\n"
                "Введите имя питомца:"
            ),
            keyboard=order_form_keyboard("pet_name")
        )

        await state.update_data(
            cart_data=cart_data,
            user_id=user.id
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_start_order: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router_smi.message(OrderFormSMI.waiting_pet_name)
async def smi_process_pet_name(message: Message, state: FSMContext):
    """Обработка имени питомца"""
    pet_name = message.text.strip()

    if len(pet_name) < 2:
        await message_manager.update_message(
            user_id=message.from_user.id,
            message_or_callback=message,
            text=(
                "🛎️ <b>Оформление заказа</b>\n\n"
                "❌ Имя слишком короткое (минимум 2 символа)\n\n"
                "Введите имя питомца:"
            ),
            keyboard=order_form_keyboard("pet_name")
        )
        return

    await state.update_data(pet_name=pet_name)
    await state.set_state(OrderFormSMI.waiting_address)

    # Получаем информацию о пользователе
    data = await state.get_data()
    user_id = data.get("user_id")
    user_info = await user_service.get_user_info(user_id)

    # Проверяем есть ли старый адрес
    old_address = user_info.get("address") if user_info else None

    if old_address:
        address_text = (
            f"🛎️ <b>Оформление заказа</b>\n\n"
            f"✅ Имя питомца: {pet_name}\n\n"
            f"Шаг 2 из 3\n\n"
            f"Предыдущий адрес:\n{old_address}\n\n"
            "Использовать этот адрес? (да/нет)\n"
            "Или введите новый адрес:"
        )
    else:
        address_text = (
            f"🛎️ <b>Оформление заказа</b>\n\n"
            f"✅ Имя питомца: {pet_name}\n\n"
            f"Шаг 2 из 3\n\n"
            "Введите адрес доставки:\n"
            "Улица, дом, квартира, город\n\n"
            "Пример: ул. Кнез Михаилова 15, кв. 23, Белград"
        )

    await message_manager.update_message(
        user_id=message.from_user.id,
        message_or_callback=message,
        text=address_text,
        keyboard=order_form_keyboard("address")
    )


# ... (продолжение обработки заказа аналогично)

@router_smi.callback_query(F.data == "smi_order_confirm")
async def smi_confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение заказа - ПРОСТАЯ РЕАЛИЗАЦИЯ"""
    try:
        data = await state.get_data()

        # Здесь будет логика создания заказа как в оригинале
        # Но пока просто показываем успех

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=(
                "🎉 <b>Заказ успешно оформлен!</b>\n\n"
                "📞 Мы свяжемся с вами в ближайшее время.\n\n"
                "Спасибо за покупку! 🐶"
            ),
            keyboard=main_menu_keyboard()
        )

        await state.clear()
        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="main_menu",
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_confirm_order: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


# ========== ПРОФИЛЬ И ПОМОЩЬ ==========

@router_smi.callback_query(F.data == "smi_profile")
async def smi_show_profile(callback: CallbackQuery, state: FSMContext):
    """Показать профиль"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        user_info = await user_service.get_user_info(user.id)

        if user_info:
            profile_text = (
                f"👤 <b>Ваш профиль</b>\n\n"
                f"🐕 Питомец: {user_info.get('pet_name', 'Не указано')}\n"
                f"📱 Telegram: @{user_info.get('telegram_username', 'Не указан')}\n"
                f"📍 Адрес: {user_info.get('address', 'Не указан')}\n\n"
                f"🆔 ID: {user.id}\n"
                f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}"
            )
        else:
            profile_text = (
                "👤 <b>Ваш профиль</b>\n\n"
                "Данные будут заполнены после первого заказа."
            )

        await message_manager.safe_edit_message(
            user_id=callback.from_user.id,
            message=callback.message,
            text=profile_text,
            keyboard=main_menu_keyboard()
        )

        await state_manager.save_current_state(
            user_id=callback.from_user.id,
            screen="profile",
            fsm_context=state
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в smi_show_profile: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router_smi.callback_query(F.data == "smi_help")
async def smi_show_help(callback: CallbackQuery, state: FSMContext):
    """Показать помощь"""
    help_text = (
        "🐾 <b>Помощь по боту Barkery Shop</b>\n\n"
        "📦 <b>Каталог</b> - просмотр товаров по категориям\n"
        "🛒 <b>Корзина</b> - ваши выбранные товары\n"
        "👤 <b>Профиль</b> - ваши данные\n\n"
        "📱 <b>Как сделать заказ:</b>\n"
        "1. Выберите товары в каталоге\n"
        "2. Добавьте их в корзину\n"
        "3. Перейдите в корзину\n"
        "4. Оформите заказ\n\n"
        "💬 <b>Поддержка:</b> @barkery_rs"
    )

    await message_manager.safe_edit_message(
        user_id=callback.from_user.id,
        message=callback.message,
        text=help_text,
        keyboard=main_menu_keyboard()
    )

    await state_manager.save_current_state(
        user_id=callback.from_user.id,
        screen="help",
        fsm_context=state
    )

    await callback.answer()


# ========== ОБРАБОТКА НЕИЗВЕСТНЫХ КОЛБЭКОВ ==========

@router_smi.callback_query()
async def smi_handle_unknown(callback: CallbackQuery):
    """Обработка неизвестных колбэков"""
    # Игнорируем админские колбэки
    if callback.data.startswith("admin_"):
        return

    # Игнорируем колбэки для обычного интерфейса
    if callback.data in ["catalog", "cart", "profile", "help"]:
        return

    # Для всех других неизвестных колбэков возвращаем в главное меню
    await message_manager.safe_edit_message(
        user_id=callback.from_user.id,
        message=callback.message,
        text=(
            "🐕 <b>Главное меню</b>\n\n"
            "Выберите действие:"
        ),
        keyboard=main_menu_keyboard()
    )

    await callback.answer("⚠️ Эта кнопка сейчас не работает", show_alert=True)