from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.callbacks import CB

router = Router()


@router.callback_query(F.data.startswith(CB.QTY))
async def handle_quantity(callback: CallbackQuery):
    # Формат: "qty:{product_id}:{action}:{category}:{current_qty}"
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer("❌ Ошибка")
        return

    _, product_id_str, action, category, current_qty_str = parts

    try:
        product_id = int(product_id_str)
        current_qty = int(current_qty_str)
    except ValueError:
        await callback.answer("❌ Ошибка в данных")
        return

    # Изменяем количество
    if action == "inc":
        new_qty = current_qty + 1
    elif action == "dec":
        new_qty = max(1, current_qty - 1)  # Минимум 1
    else:
        await callback.answer("❌ Неизвестное действие")
        return

    # Проверяем изменилось ли количество
    if new_qty == current_qty:
        await callback.answer(f"Минимальное количество: 1")
        return

    # Обновляем сообщение с новым количеством
    from app.keyboards.user import quantity_keyboard
    from app.services.catalog import get_product

    product = await get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден")
        return

    # Создаем новую клавиатуру
    new_keyboard = quantity_keyboard(
        product_id=product_id,
        category=category,
        price=product.price,
        qty=new_qty
    )

    try:
        # Пытаемся обновить клавиатуру
        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
        await callback.answer(f"Количество: {new_qty}")
    except Exception as e:
        # Если ошибка "message not modified" - игнорируем
        if "message is not modified" in str(e):
            await callback.answer(f"Количество: {new_qty}")
        else:
            await callback.answer("❌ Ошибка обновления")