from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

# Категории и товары
CATEGORIES = ["Мотивационные лакомства", "Погрызухи", "Гипоаллергенные лакомства"]

PRODUCTS = {
    "Мотивационные лакомства": [
        {"id": "m1", "name": "Лакомство A"},
        {"id": "m2", "name": "Лакомство B"},
    ],
    "Погрызухи": [
        {"id": "p1", "name": "Погрызуха X"},
        {"id": "p2", "name": "Погрызуха Y"},
    ],
    "Гипоаллергенные лакомства": [
        {"id": "g1", "name": "Гипо A"},
        {"id": "g2", "name": "Гипо B"},
    ],
}

# Выбор категории
@router.callback_query(F.data.startswith("category:"))
async def show_products(call: CallbackQuery):
    category = call.data.split(":")[1]
    products = PRODUCTS.get(category, [])
    if not products:
        await call.answer("Нет товаров в этой категории", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(
            InlineKeyboardButton(text=f"{product['name']} ➕", callback_data=f"add:{product['id']}"),
            InlineKeyboardButton(text=f"{product['name']} ➖", callback_data=f"remove:{product['id']}")
        )
    # Кнопка перехода в корзину
    builder.button(text="🛒 Корзина", callback_data="view_cart")

    keyboard = builder.as_markup()
    await call.message.answer(f"Категория: {category}", reply_markup=keyboard)
    await call.answer()