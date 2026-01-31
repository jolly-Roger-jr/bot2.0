python3 migrate_data.py

echo -e "\n=== ОБНОВЛЯЕМ services.py ==="
mv services_new.py services.py
eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeОeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeОeee нeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeОlceeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeОeefuneeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeОeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeemy.sql import func\n/' services.py
    echo "Импорт добавлен"
fi

echo -e "\n=== АНАЛИЗИРУЕМ ПРОЦЕСС ЗАКАЗА ДЛЯ МОДИФИКАЦИИ ==="
echo "Текущие шаги заказа:"
grep -n "waiting_pet_name\|waiting_telegram_login\|waiting_address" handlers.py

echo -e "\n=== СОЗДАЕМ НОВУЮ ВЕРСИЮ handlers.py (процесс заказа) ==="
# СначалtatesGroup
from aiogram.exceptions import TelegramBadRequest

from keyboards import (
    main_menu_keyboard,
    categories_keyboard,
    products_keyboard,
    product_card_keyboard,
    cart_keyboard,
    order_confirmation_keyboard
)
from services import cart_service, catalog_service, user_service
from database import get_session, Product, CartItem, User
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = Router()

# Храним предварительные количества для каждого пользователя и товара
temp_quantities = {}

# ========== СОСТОЯНИЯ ДЛЯ ЗАКАЗА ==========

class OrderForm(StatesGroup):
    waiting_pet_name = State()
    waiting_address = State()
    waiting_telegram_login = State()  # Только если нет telegram_username
    waiting_address_change = State()  # Для проверки изменения адреса

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_temp_quantity_key(user_id: int, product_id: int) -> str:
    """Ключ для хранения временного количества"""
    return f"{user_id}_{product_id}"

def update_temp_quantity(user_id: int, product_id: int, delta: int) -> int:
    """Обновить временное количество с проверками"""
    key = get_temp_quantity_key(user_id, product_id)
    current = temp_quantities.get(key, 0)
    new_quantity = current + delta
    
    # Не может быть меньше 0
    if new_quantity < 0:
        new_quantity = 0
    
    temp_quantities[key] = new_quantity
    return new_quantity

def reset_temp_quantity(user_id: int, product_id: int):
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
        await callback.message.delete()
        
        if product.get('image_url'):
            # Отправляем фото с подписью
            await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=product['image_url'],
                caption=caption,
                reply_markup=keyboard
            )
        else:
            # Отправляем текстовое сообщение
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=caption,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Ошибка отправки товара: {e}")
        # Fallback: отправляем текстовое сообщение
        await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=caption,
            reply_markup=keyboard
        )

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start"""
    try:
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
            reply_markup=main_menu_keyboard()
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

# ========== ГЛАВНОЕ МЕНЮ ==========

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """Главное меню"""
    await safe_edit_message(
        callback,
        "🐕 Главное меню\n\nВыберите действие:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "catalog")
async def show_categories(callback: CallbackQuery):
    """Показать категории"""
    try:
        categories = await catalog_service.get_categories()
        
        if not categories:
            await safe_edit_message(
                callback,
                "📦 Каталог\n\nКатегории пока не добавлены."
            )
            return
        
        await safe_edit_message(
            callback,
            "📦 Каталог\n\nВыберите категорию:",
            reply_markup=categories_keyboard(categories)
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа категорий: {e}")
        await callback.answer("❌ Ошибка загрузки категорий", show_alert=True)

@router.callback_query(F.data.startswith("category:"))
async def show_products(callback: CallbackQuery):
    """Показать товары категории"""
    try:
        category_id = int(callback.data.split(":")[1])
        products = await catalog_service.get_products_by_category(category_id)
        
        if not products:
            await safe_edit_message(
                callback,
                "📭 Товары\n\nВ этой категории пока нет товаров."
            )
            return
        
        await safe_edit_message(
            callback,
            "📦 Товары\n\nВыберите товар:",
            reply_markup=products_keyboard(products, category_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа товаров: {e}")
        await callback.answer("❌ Ошибка загрузки товаров", show_alert=True)

@router.callback_query(F.data.startswith("product:"))
async def show_product(callback: CallbackQuery):
    """Показать карточку товара с корректной обработкой изображений"""
    try:
        parts = callback.data.split(":")
        product_id = int(parts[1])
        category_id = int(parts[2])

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

        # Получаем временное количество (предварительное)
        temp_key = get_temp_quantity_key(callback.from_user.id, product_id)
        temp_qty = temp_quantities.get(temp_key, 0)

        # Формируем описание/подпись
        description = product.get("description", "") or ""
        caption = (
            f"🦴 {product['name']}\n\n"
            f"{description}\n\n"
        )
        
        # Отображение цены в зависимости от типа товара
        if product.get('unit_type', 'grams') == 'grams':
            price_text = f"💰 Цена: {product['price']} RSD/100г\n"
            stock_text = f"📦 В наличии: {product['stock_grams']}г\n"
            cart_text = f"🛒 В корзине: {current_in_cart}г\n"
        else:
            price_text = f"💰 Цена: {product['price']} RSD/шт\n"
            stock_text = f"📦 В наличии: {product['stock_grams']}шт\n"
            cart_text = f"🛒 В корзине: {current_in_cart}шт\n"
        
        caption += price_text
        caption += stock_text
        caption += cart_text
        caption += "\nВыберите количество:"

        keyboard = product_card_keyboard(
            product_id, 
            category_id, 
            temp_qty, 
            product.get("unit_type", "grams"), 
            product.get("measurement_step", 100)
        )
        
        # Отправляем товар с изображением или без
        await send_product_with_image(callback, product, caption, keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка показа товара: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)

@router.callback_query(F.data.startswith("back_to_products:"))
async def back_to_products(callback: CallbackQuery):
    """Назад к товарам категории - КОРРЕКТНАЯ РЕАЛИЗАЦИЯ"""
    try:
        category_id = int(callback.data.split(":")[1])
        
        # Получаем товары категории
        products = await catalog_service.get_products_by_category(category_id)
        
        if not products:
            await safe_edit_message(
                callback,
                "📭 Товары\n\nВ этой категории пока нет товаров."
            )
            return
        
        # Используем безопасное редактирование для корректного возврата
        await safe_edit_message(
            callback,
            "📦 Товары\n\nВыберите товар:",
            reply_markup=products_keyboard(products, category_id)
        )
        
    except Exception as e:
        logger.error(f"Ошибка возврата к товарам: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

# ========== УПРАВЛЕНИЕ КОЛИЧЕСТВОМ ==========

@router.callback_query(F.data.startswith("qty_"))
async def handle_quantity(callback: CallbackQuery):
    """Обработка изменения предварительного количества с обновлением фото"""
    try:
        parts = callback.data.split(":")
        action = parts[0]
        product_id = int(parts[1])
        category_id = int(parts[2])
        
        if action == "qty_info":
            await callback.answer("📊 Предварительное количество")
            return
        
        # Получаем данные о товаре
        product = await catalog_service.get_product(product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return
        
        user = await cart_service.get_or_create_user(callback.from_user.id)
        
        # Определяем дельту с учетом шага измерения товара
        measurement_step = product.get('measurement_step', 100)
        delta = -measurement_step if action == "qty_dec" else measurement_step
        
        # Получаем текущее количество в корзине
        async with get_session() as session:
            stmt = select(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.product_id == product_id
            )
            result = await session.execute(stmt)
            cart_item = result.scalar_one_or_none()
            current_in_cart = cart_item.quantity if cart_item else 0
        
        # Получаем текущее временное количество
        temp_key = get_temp_quantity_key(callback.from_user.id, product_id)
        current_temp = temp_quantities.get(temp_key, 0)
        
        # Проверяем общее количество (в корзине + новое временное)
        new_temp = current_temp + delta
        
        # Не может быть меньше 0
        if new_temp < 0:
            await callback.answer("❌ Количество не может быть меньше 0")
            return
        
        # Проверяем максимальное доступное количество
        total_qty = current_in_cart + new_temp
        if total_qty > product['stock_grams']:
            max_can_add = product['stock_grams'] - current_in_cart
            new_temp = max_can_add
            unit_suffix = "г" if product.get('unit_type', 'grams') == 'grams' else "шт"
            await callback.answer(f"❌ Максимально можно добавить: {max_can_add}{unit_suffix}", show_alert=True)
            if max_can_add <= 0:
                return
        
        # Обновляем временное количество
        temp_quantities[temp_key] = new_temp
        
        # Формируем описание/подпись
        description = product.get("description", "") or ""
        caption = (
            f"🦴 {product['name']}\n\n"
            f"{description}\n\n"
        )
        
        # Отображение цены в зависимости от типа товара
        if product.get('unit_type', 'grams') == 'grams':
            price_text = f"💰 Цена: {product['price']} RSD/100г\n"
            stock_text = f"📦 В наличии: {product['stock_grams']}г\n"
            cart_text = f"🛒 В корзине: {current_in_cart}г\n"
        else:
            price_text = f"💰 Цена: {product['price']} RSD/шт\n"
            stock_text = f"📦 В наличии: {product['stock_grams']}шт\n"
            cart_text = f"🛒 В корзине: {current_in_cart}шт\n"
        
        caption += price_text
        caption += stock_text
        caption += cart_text
        caption += "\nВыберите количество:"

        keyboard = product_card_keyboard(
            product_id, 
            category_id, 
            new_temp, 
            product.get("unit_type", "grams"), 
            product.get("measurement_step", 100)
        )
        
        # Обновляем сообщение
        try:
            if callback.message.photo:
                # Обновляем подпись фото
                await callback.message.edit_caption(
                    caption=caption,
                    reply_markup=keyboard
                )
            else:
                # Обновляем текстовое сообщение
                await callback.message.edit_text(
                    text=caption,
                    reply_markup=keyboard
                )
        except TelegramBadRequest as e:
            # Если сообщение устарело, отправляем новое
            logger.warning(f"Сообщение устарело, отправляю новое: {e}")
            await send_product_with_image(callback, product, caption, keyboard)
        
        # Показываем информацию о предварительном количестве
        unit_suffix = "г" if product.get('unit_type', 'grams') == 'grams' else "шт"
        await callback.answer(f"Предварительное количество: {new_temp}{unit_suffix}")
            
    except Exception as e:
        logger.error(f"Ошибка изменения количества: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.callback_query(F.data.startswith("cart_add:"))
async def add_to_cart(callback: CallbackQuery):
    """Добавить товар в корзину (предварительное количество)"""
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
            reset_temp_quantity(callback.from_user.id, product_id)

            # Обновляем отображение с новым количеством в корзине
            product = await catalog_service.get_product(product_id)

            # Получаем обновленное количество в корзине
            async with get_session() as session:
                stmt = select(CartItem).where(
                    CartItem.user_id == user.id,
                    CartItem.product_id == product_id
                )
                result2 = await session.execute(stmt)
                cart_item = result2.scalar_one_or_none()
                current_in_cart = cart_item.quantity if cart_item else 0

            # Формируем описание/подпись
            description = product.get("description", "") or ""
            caption = (
                f"🦴 {product['name']}\n\n"
                f"{description}\n\n"
            )
            
            # Отображение цены в зависимости от типа товара
            if product.get('unit_type', 'grams') == 'grams':
                price_text = f"💰 Цена: {product['price']} RSD/100г\n"
                stock_text = f"📦 В наличии: {product['stock_grams']}г\n"
                cart_text = f"✅ В корзине: {current_in_cart}г\n"
            else:
                price_text = f"💰 Цена: {product['price']} RSD/шт\n"
                stock_text = f"📦 В наличии: {product['stock_grams']}шт\n"
                cart_text = f"✅ В корзине: {current_in_cart}шт\n"
            
            caption += price_text
            caption += stock_text
            caption += cart_text
            caption += f"\nТовар добавлен в корзину!"

            # Обновляем сообщение с сброшенным счетчиком
            keyboard = product_card_keyboard(
                product_id, 
                category_id, 
                0, 
                product.get("unit_type", "grams"), 
                product.get("measurement_step", 100)
            )
            
            # Обновляем сообщение
            try:
                if callback.message.photo:
                    await callback.message.edit_caption(
                        caption=caption,
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        text=caption,
                        reply_markup=keyboard
                    )
            except TelegramBadRequest:
                await send_product_with_image(callback, product, caption, keyboard)
            
            unit_suffix = "г" if product.get("unit_type", "grams") == "grams" else "шт"
            await callback.answer(f"✅ Добавлено в корзину: {quantity}{unit_suffix}")
        else:
            await callback.answer(result["error"], show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        await callback.answer("❌ Ошибка добавления", show_alert=True)

# ========== КОРЗИНА ==========

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    """Показать корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await safe_edit_message(
                callback,
                "🛒 Корзина пуста\n\nДобавьте товары из каталога!"
            )
            return
        
        # Формируем текст с списком товаров
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        cart_text = (
            f"🛒 Ваша корзина\n\n"
            f"{items_text}\n\n"
            f"📦 Товаров: {cart_data['total_items']} шт.\n"
            f"💰 Итого: {cart_data['total_price']:.0f} RSD"
        )
        
        await safe_edit_message(
            callback,
            cart_text,
            reply_markup=cart_keyboard(cart_data["items"], cart_data["total_price"])
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа корзины: {e}")
        await callback.answer("❌ Ошибка загрузки корзины", show_alert=True)

@router.callback_query(F.data == "cart_clear")
async def clear_cart(callback: CallbackQuery):
    """Очистить корзину"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        result = await cart_service.clear_cart(user.id)
        
        if result["success"]:
            # Также очищаем все временные количества пользователя
            user_prefix = f"{callback.from_user.id}_"
            keys_to_remove = [k for k in temp_quantities.keys() if k.startswith(user_prefix)]
            for key in keys_to_remove:
                del temp_quantities[key]
            
            await safe_edit_message(
                callback,
                f"✅ {result['message']}\n\nКорзина пуста."
            )
        await callback.answer(result["message"])
        
    except Exception as e:
        logger.error(f"Ошибка очистки корзины: {e}")
        await callback.answer("❌ Ошибка очистки", show_alert=True)

# ========== ОБРАБОТКА ЗАКАЗА (ОБНОВЛЕННАЯ ВЕРСИЯ) ==========

@router.callback_query(F.data == "order_create")
async def start_order(callback: CallbackQuery, state: FSMContext):
    """Начать оформление заказа - ОБНОВЛЕННАЯ ВЕРСИЯ"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        cart_data = await cart_service.get_cart(user.id)
        
        if not cart_data["items"]:
            await callback.answer("🛒 Корзина пуста!", show_alert=True)
            return
        
        # Получаем информацию о пользователе
        user_info = await user_service.get_user_info(user.id)
        
        # Сохраняем данные о корзине и пользователе
        await state.update_data(
            user_id=user.id,
            cart_items=cart_data["items"],
            total_amount=cart_data["total_price"],
            user_info=user_info
        )
        
        items_text = "\n".join([
            f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
            for item in cart_data["items"]
        ])
        
        # Шаг 1: Имя питомца (всегда спрашиваем)
        await state.set_state(OrderForm.waiting_pet_name)
        
        # Если у пользователя уже есть имя питомца, показываем его
        current_pet_name = user_info.get('pet_name') if user_info else None
        if current_pet_name:
            order_text = (
                "🛎️ Оформление заказа\n\n"
                f"Ваш заказ:\n{items_text}\n\n"
                f"Итого: {cart_data['total_price']:.0f} RSD\n\n"
                f"Текущее имя питомца: {current_pet_name}\n\n"
                "🐕 Шаг 1 из 3: Введите имя питомца (или отправьте '+' чтобы оставить текущее):"
            )
        else:
            order_text = (
                "🛎️ Оформление заказа\n\n"
                f"Ваш заказ:\n{items_text}\n\n"
                f"Итого: {cart_data['total_price']:.0f} RSD\n\n"
                "🐕 Шаг 1 из 3: Введите имя питомца:"
            )
        
        await safe_edit_message(callback, order_text)
        
    except Exception as e:
        logger.error(f"Ошибка начала заказа: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

@router.message(OrderForm.waiting_pet_name)
async def process_pet_name(message: Message, state: FSMContext):
    """Обработка имени питомца"""
    pet_name = message.text.strip()
    data = await state.get_data()
    user_info = data.get('user_info', {})
    
    # Проверяем, хочет ли пользователь оставить текущее имя
    if pet_name == '+' and user_info.get('pet_name'):
        pet_name = user_info['pet_name']
    else:
        if len(pet_name) < 2:
            # Удаляем предыдущее сообщение о запросе имени
            try:
                await message.delete()
            except:
                pass  # Игнорируем ошибки удаления

            await message.answer("❌ Слишком короткое имя. Введите имя питомца:")
            return
    
    await state.update_data(pet_name=pet_name)
    
    # Шаг 2: Адрес доставки
    await state.set_state(OrderForm.waiting_address)
    
    # Проверяем есть ли у пользователя старый адрес
    old_address = user_info.get('address') if user_info else None
    
    if old_address:
        address_text = (
            f"✅ Имя питомца принято: {pet_name}\n\n"
            f"📍 Шаг 2 из 3: Адрес доставки\n\n"
            f"Предыдущий адрес:\n{old_address}\n\n"
            "Использовать этот адрес? (да/нет)\n"
            "Или введите новый адрес доставки:"
        )
        await state.set_state(OrderForm.waiting_address_change)
    else:
        address_text = (
            f"✅ Имя питомца принято: {pet_name}\n\n"
            "📍 Шаг 2 из 3: Введите адрес доставки:\n"
            "Улица, дом, квартира, город\n\n"
            "Пример: ул. Кнез Михаилова 15, кв. 23, Белград"
        )
        await state.set_state(OrderForm.waiting_address)
    
    await message.answer(address_text)

@router.message(OrderForm.waiting_address_change)
async def process_address_change(message: Message, state: FSMContext):
    """Обработка изменения адреса"""
    response = message.text.strip().lower()
    data = await state.get_data()
    user_info = data.get('user_info', {})
    
    if response in ['да', 'д', 'yes', 'y', '+']:
        # Используем старый адрес
        address = user_info.get('address', '')
        if not address:
            await message.answer("❌ Старый адрес не найден. Введите адрес доставки:")
            await state.set_state(OrderForm.waiting_address)
            return
        
        await state.update_data(address=address)
        
        # Переходим к проверке telegram login
        await check_telegram_login(message, state)
        
    elif response in ['нет', 'н', 'no', 'n']:
        # Запрашиваем новый адрес
        await message.answer(
            "Введите новый адрес доставки:\n"
            "Улица, дом, квартира, город\n\n"
            "Пример: ул. Кнез Михаилова 15, кв. 23, Белград"
        )
        await state.set_state(OrderForm.waiting_address)
    else:
        # Пользователь ввел новый адрес напрямую
        address = message.text.strip()
        if len(address) < 10:
            await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
            return
        
        await state.update_data(address=address)
        
        # Переходим к проверке telegram login
        await check_telegram_login(message, state)

@router.message(OrderForm.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка адреса доставки"""
    address = message.text.strip()
    
    if len(address) < 10:
        # Удаляем предыдущее сообщение о запросе адреса
        try:
            await message.delete()
        except:
            pass  # Игнорируем ошибки удаления

        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return
    
    await state.update_data(address=address)
    
    # Переходим к проверке telegram login
    await check_telegram_login(message, state)

async def check_telegram_login(message: Message, state: FSMContext):
    """Проверка наличия telegram логина"""
    data = await state.get_data()
    user_info = data.get('user_info', {})
    
    # Проверяем есть ли у пользователя telegram_username
    telegram_username = user_info.get('telegram_username')
    
    if telegram_username:
        # У пользователя уже есть логин, пропускаем этот шаг
        await state.update_data(telegram_login=telegram_username)
        
        # Переходим к подтверждению заказа
        await show_order_confirmation(message, state)
    else:
        # Запрашиваем telegram login
        await state.set_state(OrderForm.waiting_telegram_login)
        await message.answer(
            "📱 Шаг 3 из 3: Введите ваш Telegram login (без @):\n"
            "Например: ivanov_ivan"
        )

@router.message(OrderForm.waiting_telegram_login)
async def process_telegram_login(message: Message, state: FSMContext):
    """Обработка Telegram логина"""
    telegram_login = message.text.strip().replace("@", "")
    
    if len(telegram_login) < 3:
        # Удаляем предыдущее сообщение о запросе логина
        try:
            await message.delete()
        except:
            pass  # Игнорируем ошибки удаления

        await message.answer("❌ Слишком короткий login. Введите Telegram login:")
        return
    
    await state.update_data(telegram_login=telegram_login)
    
    # Переходим к подтверждению заказа
    await show_order_confirmation(message, state)

async def show_order_confirmation(message: Message, state: FSMContext):
    """Показать подтверждение заказа"""
    data = await state.get_data()
    
    # Формируем подтверждение
    items_text = "\n".join([
        f"• {item['product_name']}: {item['quantity']}{'г' if item.get('unit_type', 'grams') == 'grams' else 'шт'} - {item['total_price']:.0f} RSD"
        for item in data["cart_items"]
    ])
    
    confirmation_text = (
        "✅ Подтверждение заказа\n\n"
        f"🐕 Питомец: {data['pet_name']}\n"
        f"📱 Telegram: @{data['telegram_login']}\n"
        f"📍 Адрес доставки: {data['address']}\n\n"
        f"📋 Состав заказа:\n{items_text}\n\n"
        f"💰 Итого к оплате: {data['total_amount']:.0f} RSD\n\n"
        "Подтвердите заказ:"
    )
    
    await message.answer(
        confirmation_text,
        reply_markup=order_confirmation_keyboard()
    )

@router.callback_query(F.data == "order_confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и создание заказа"""
    try:
        data = await state.get_data()
        
        # Обновляем информацию о пользователе в БД
        user_update_data = {
            "pet_name": data.get("pet_name"),
            "telegram_username": data.get("telegram_login"),
            "address": data.get("address")  # Сохраняем адрес для обратной совместимости
        }
        
        # Очищаем None значения
        user_update_data = {k: v for k, v in user_update_data.items() if v is not None}
        
        # Обновляем пользователя
        await user_service.update_user_info(data["user_id"], **user_update_data)
        
        async with get_session() as session:
            # Создаем заказ
            from database import Order, OrderItem
            import datetime
            
            order = Order(
                user_id=data["user_id"],
                customer_name=data["pet_name"],
                phone=f"@{data['telegram_login']}",
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
            await cart_service.clear_cart(data["user_id"])
            
            # Очищаем временные количества пользователя
            user_prefix = f"{data['user_id']}_"
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
        await callback.answer("❌ Ошибка создания заказа", show_alert=True)

# ========== ПРОФИЛЬ ==========

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Показать профиль"""
    try:
        user = await cart_service.get_or_create_user(callback.from_user.id)
        user_info = await user_service.get_user_info(user.id)
        
        if not user_info:
            profile_text = (
                f"👤 Ваш профиль\n\n"
                f"🆔 ID: {user.id}\n"
                f"📅 Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}\n\n"
                "Данные будут заполнены после первого заказа."
            )
        else:
            profile_text = (
                f"👤 Ваш профиль\n\n"
                f"🐕 Питомец: {user_info.get('pet_name', 'Не указано')}\n"
                f"📱 Telegram: @{user_info.get('telegram_username', 'Не указан')}\n"
                f"📞 Телефон: {user_info.get('phone', 'Не указан')}\n"
                f"🐶 Порода: {user_info.get('dog_breed', 'Не указана')}\n"
                f"⚠️ Аллергии: {user_info.get('allergies', 'Не указаны')}\n"
                f"📝 Примечания: {user_info.get('notes', 'Нет')}\n"
                f"📍 Адрес: {user_info.get('address', 'Не указан')}\n"
                f"🆔 ID: {user.id}\n"
                f"📅 Зарегистрирован: {user.created_at.strftime('%d.%m.%Y')}\n"
            )
        
        await safe_edit_message(
            callback,
            profile_text,
            reply_markup=main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка показа профиля: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)

# ========== ПОМОЩЬ ==========

@router.callback_query(F.data == "help")
async def handle_help(callback: CallbackQuery):
    """Показать помощь"""
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
    
    from keyboards import help_keyboard
    await safe_edit_message(
        callback,
        help_text,
        reply_markup=help_keyboard()
    )
    await callback.answer()

# ========== ОБРАБОТКА НЕИЗВЕСТНЫХ КОЛБЭКОВ ==========

@router.callback_query()
async def handle_unknown_callback(callback: CallbackQuery):
    """Обработка неизвестных callback-запросов"""
    # Игнорируем админские колбэки (они обрабатываются в админском роутере)
    if callback.data.startswith("admin_"):
        # Пропускаем админские колбэки
        return
    
    logger.warning(f"Неизвестный колбэк: {callback.data}")
    await callback.answer("⚠️ Эта кнопка сейчас не работает", show_alert=True)
    await safe_edit_message(
        callback,
        "🐕 Главное меню\n\nВыберите действие:",
        reply_markup=main_menu_keyboard()
    )
