# app/handlers/user/qty.py - СОЗДАЙТЕ ЭТОТ ФАЙЛ
from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from app.services import catalog
from app.keyboards.user import quantity_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data.startswith("qty:"))
async def handle_quantity_change(callback: CallbackQuery):
    """Обработка изменения количества товара с шагом 100г"""
    logger.info(f"📨 Получен callback qty: {callback.data}")

    # Формат: "qty:{product_id}:{action}:{category}:{current_qty}"
    parts = callback.data.split(":")
    logger.info(f"📊 Частей в callback: {len(parts)} -> {parts}")

    if len(parts) != 5:
        logger.error(f"❌ Неправильный формат: {len(parts)} частей вместо 5")
        await callback.answer("❌ Ошибка формата", show_alert=True)
        return

    _, product_id_str, action, category, current_qty_str = parts

    try:
        product_id = int(product_id_str)
        current_qty = int(current_qty_str)
        logger.info(f"📦 Парсинг: product_id={product_id}, action={action}, category={category}, qty={current_qty}")
    except ValueError as e:
        logger.error(f"❌ Ошибка парсинга: {e}")
        await callback.answer("❌ Ошибка в данных", show_alert=True)
        return

    # Изменяем количество с шагом 100г
    if action == "dec_100":
        new_qty = max(100, current_qty - 100)  # Минимум 100г
        logger.info(f"➖ Уменьшение: {current_qty} -> {new_qty}")
    elif action == "inc_100":
        new_qty = current_qty + 100
        logger.info(f"➕ Увеличение: {current_qty} -> {new_qty}")
    else:
        logger.error(f"❌ Неизвестное действие: {action}")
        await callback.answer("❌ Неизвестное действие", show_alert=True)
        return

    # Получаем информацию о товаре
    product = await catalog.get_product(product_id)
    if not product:
        logger.error(f"❌ Товар не найден: {product_id}")
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    logger.info(f"✅ Товар найден: {product.name}, остаток: {product.stock_grams}г")

    # Проверяем доступное количество
    if new_qty > product.stock_grams:
        logger.warning(f"⚠️ Недостаточно: нужно {new_qty}, есть {product.stock_grams}")
        await callback.answer(f"❌ Доступно только {product.stock_grams}г", show_alert=True)
        return

    # Обновляем клавиатуру с новым количеством
    try:
        logger.info(f"🔄 Обновление клавиатуры: {new_qty}г")
        await callback.message.edit_reply_markup(
            reply_markup=quantity_keyboard(product_id, category, product.price, new_qty)
        )
        logger.info(f"✅ Клавиатура обновлена")
        await callback.answer(f"Количество: {new_qty}г")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Ошибка обновления: {error_msg}")
        if "message is not modified" in error_msg:
            await callback.answer(f"Количество: {new_qty}г")
        else:
            await callback.answer("❌ Ошибка обновления", show_alert=True)