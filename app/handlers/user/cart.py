from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .catalog import PRODUCTS, CATEGORIES  # относительный импорт внутри пакета user

router = Router()

# Добавление товара в корзину
@router.callback_query(F.data.startswith("add:"))
async def add_to_cart(call: CallbackQuery, state: FSMContext):
    item = call.data.split("add:")[1]
    data = await state.get_data()
    cart = data.get("cart", {})
    cart[item] = cart.get(item, 0) + 1
    await state.update_data(cart=cart)
    await call.answer(f"Добавлено: {item}")

# Удаление товара из корзины
@router.callback_query(F.data.startswith("remove:"))
async def remove_from_cart(call: CallbackQuery, state: FSMContext):
    item = call.data.split("remove:")[1]
    data = await state.get_data()
    cart = data.get("cart", {})
    if item in cart:
        if cart[item] > 1:
            cart[item] -= 1
            await call.answer(f"Удалено одно: {item}")
        else:
            del cart[item]
            await call.answer(f"Удалено: {item}")
        await state.update_data(cart=cart)
    else:
        await call.answer("Этот товар не в корзине.", show_alert=True)

# Просмотр корзины
@router.callback_query(F.data == "view_cart")
async def view_cart(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", {})
    if not cart:
        await call.message.answer("Ваша корзина пуста.")
        await call.answer()
        return

    text_lines = ["Ваша корзина:"]
    for item, qty in cart.items():
        text_lines.append(f"{item}: {qty}")
    text = "\n".join(text_lines)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Очистить корзину", callback_data="clear_cart"),
        InlineKeyboardButton(text="Назад к категориям", callback_data="back_to_categories")
    )
    keyboard = builder.as_markup()

    await call.message.answer(text, reply_markup=keyboard)
    await call.answer()

# Очистка корзины
@router.callback_query(F.data == "clear_cart")
async def clear_cart(call: CallbackQuery, state: FSMContext):
    await state.update_data(cart={})
    await call.message.answer("Корзина очищена.")
    await call.answer()

# Возврат к категориям
@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(call: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for category in CATEGORIES:
        builder.button(text=category, callback_data=f"category:{category}")
    keyboard = builder.as_markup()
    await call.message.answer("Выберите категорию товаров:", reply_markup=keyboard)
    await call.answer()