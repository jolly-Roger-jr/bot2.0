# app/handlers/user/cart.py - ПОЛНЫЙ ФАЙЛ
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from app.callbacks import CB
from app.services.cart import (
    add_to_cart,
    get_cart_items,
    clear_cart,
    get_cart_total,
    update_cart_item,
    remove_from_cart,
    validate_cart_for_order
)
from app.keyboards.user import cart_keyboard, cart_item_management_keyboard

router = Router()


@router.message(Command("cart"))
async def show_cart_cmd(message: Message):
    """Показать корзину с проверкой доступности товаров"""
    result = await get_cart_total(message.from_user.id)

    if not result.get('success', False):
        if 'unavailable_items' in result:
            # Есть недоступные товары
            text = "🔄 *Корзина обновлена*\n\n"
            text += "Некоторые товары стали недоступны:\n"

            for item in result['unavailable_items']:
                if item['available'] > 0:
                    text += f"• {item['name']}: доступно {item['available']}г (было {item['requested']}г)\n"
                else:
                    text += f"• {item['name']}: товар закончился\n"

            text += "\nКорзина автоматически обновлена."
            await message.answer(text, parse_mode="Markdown")

            # Показываем обновленную корзину
            result = await get_cart_total(message.from_user.id)
        else:
            await message.answer("🛒 Корзина пуста")
            return

    # Показываем корзину
    items = result.get('items', [])
    total = result.get('total', 0)

    if not items:
        await message.answer("🛒 Корзина пуста")
        return

    text = "🛒 *Ваша корзина:*\n\n"

    for item in items:
        if 'product_name' in item:
            subtotal = item['price_per_100g'] * item['quantity'] / 100
            text += f"• *{item['product_name']}*\n"
            text += f"  {item['quantity']}г × {item['price_per_100g']} RSD/100г = {int(subtotal)} RSD\n\n"

    text += f"*Итого:* {int(total)} RSD"

    await message.answer(text, parse_mode="Markdown", reply_markup=cart_keyboard())


@router.callback_query(F.data.startswith(CB.CART_ADD))
async def add_to_cart_cb(callback: CallbackQuery):
    """Добавление товара в корзину с обработкой ошибок"""
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return

    _, _, product_id_str, qty_str, _ = parts

    try:
        product_id = int(product_id_str)
        quantity = int(qty_str)
    except ValueError:
        await callback.answer("❌ Ошибка в данных", show_alert=True)
        return

    result = await add_to_cart(
        user_id=callback.from_user.id,
        product_id=product_id,
        quantity=quantity
    )

    if result['success']:
        await callback.answer(f"✅ Добавлено {quantity}г")

        # Возвращаем к категории товаров
        from app.handlers.user.catalog import show_products
        fake_callback = type('FakeCallback', (), {
            'data': f"category:{parts[4]}",
            'from_user': callback.from_user,
            'message': callback.message,
            'answer': callback.answer
        })()

        await show_products(fake_callback)
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        if 'available_qty' in result and result['available_qty'] > 0:
            await callback.answer(
                f"⚠️ {error_msg}. Доступно {result['available_qty']}г",
                show_alert=True
            )
        else:
            await callback.answer(f"❌ {error_msg}", show_alert=True)


@router.callback_query(F.data == "show_cart")
async def show_cart_from_button(callback: CallbackQuery):
    """Обработчик кнопки корзины из меню"""
    result = await get_cart_total(callback.from_user.id)

    if not result.get('success', False):
        if 'error' in result and result['error'] == 'Корзина пуста':
            await callback.answer("🛒 Корзина пуста", show_alert=True)
        else:
            await callback.answer("❌ Ошибка загрузки корзины", show_alert=True)
        return

    items = result.get('items', [])
    total = result.get('total', 0)

    if not items:
        await callback.answer("🛒 Корзина пуста", show_alert=True)
        return

    text = "🛒 *Ваша корзина:*\n\n"

    for item in items:
        if 'product_name' in item:
            subtotal = item['price_per_100g'] * item['quantity'] / 100
            text += f"• *{item['product_name']}*\n"
            text += f"  {item['quantity']}г × {item['price_per_100g']} RSD/100г = {int(subtotal)} RSD\n\n"

    text += f"*Итого:* {int(total)} RSD"

    await callback.message.answer(text, parse_mode="Markdown", reply_markup=cart_keyboard())
    await callback.answer()


@router.callback_query(F.data == CB.CART_CLEAR)
async def clear_cart_cb(callback: CallbackQuery):
    """Очистка корзины"""
    result = await clear_cart(callback.from_user.id)

    if result['success']:
        await callback.message.edit_text("🗑 Корзина очищена")
    else:
        await callback.answer("❌ Ошибка при очистке корзины", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("cart:update:"))
async def update_cart_item_cb(callback: CallbackQuery):
    """Обновление количества товара в корзине с шагом 100г"""
    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return

    _, _, product_id_str, new_qty_str = parts

    try:
        product_id = int(product_id_str)
        new_qty = int(new_qty_str)
    except ValueError:
        await callback.answer("❌ Ошибка в данных", show_alert=True)
        return

    # Проверяем, чтобы количество было кратно 100г и не меньше 100г
    if new_qty < 100:
        new_qty = 100

    if new_qty % 100 != 0:
        new_qty = (new_qty // 100) * 100

    result = await update_cart_item(
        user_id=callback.from_user.id,
        product_id=product_id,
        new_quantity=new_qty
    )

    if result['success']:
        await callback.answer(f"✅ Обновлено: {new_qty}г")
        await show_cart_from_button(callback)
    else:
        error_msg = result.get('error', 'Неизвестная ошибка')
        if 'available_qty' in result:
            await callback.answer(
                f"❌ {error_msg}. Доступно: {result['available_qty']}г",
                show_alert=True
            )
        else:
            await callback.answer(f"❌ {error_msg}", show_alert=True)


@router.callback_query(F.data.startswith("cart:remove:"))
async def remove_cart_item_cb(callback: CallbackQuery):
    """Удаление товара из корзины"""
    product_id = int(callback.data.split(":")[2])

    result = await remove_from_cart(
        user_id=callback.from_user.id,
        product_id=product_id
    )

    if result['success']:
        await callback.answer("✅ Товар удален из корзины")
        await show_cart_from_button(callback)
    else:
        await callback.answer("❌ Ошибка при удалении", show_alert=True)


@router.callback_query(F.data.startswith("cart:manage:"))
async def manage_cart_item(callback: CallbackQuery):
    """Управление конкретным товаром в корзине"""
    product_id = int(callback.data.split(":")[2])

    items = await get_cart_items(callback.from_user.id)

    for item in items:
        if item.product_id == product_id and item.product:
            keyboard = cart_item_management_keyboard(
                product_id,
                item.quantity,
                item.product.stock_grams
            )

            await callback.message.answer(
                f"✏️ *Управление товаром:* {item.product.name}\n\n"
                f"*Количество в корзине:* {item.quantity}г\n"
                f"*Цена:* {item.product.price} RSD/100г\n"
                f"*Доступно:* {item.product.stock_grams}г\n"
                f"*Стоимость:* {item.product.price * item.quantity / 100:.0f} RSD",
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            await callback.answer()
            return

    await callback.answer("❌ Товар не найден в корзине", show_alert=True)


@router.callback_query(F.data == "cart:check_availability")
async def check_cart_availability(callback: CallbackQuery):
    """Проверка доступности товаров в корзине"""
    result = await validate_cart_for_order(callback.from_user.id)

    if not result['success']:
        if 'unavailable_items' in result:
            text = "⚠️ *Проверка наличия*\n\n"
            text += "Обнаружены проблемы:\n"

            for item in result['unavailable_items']:
                if item['available'] > 0:
                    text += f"• {item['name']}: доступно {item['available']}г\n"
                else:
                    text += f"• {item['name']}: товар закончился\n"

            await callback.message.answer(text, parse_mode="Markdown")
        else:
            await callback.answer(result.get('error', 'Ошибка проверки'), show_alert=True)
    else:
        total = result.get('total', 0)
        await callback.answer(
            f"✅ Все товары доступны! Итого: {int(total)} RSD",
            show_alert=True
        )

    await callback.answer()