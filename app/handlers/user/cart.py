from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from app.callbacks import CB
from app.services.cart import add_to_cart, get_cart_items, clear_cart
from app.keyboards.user import cart_keyboard

router = Router()


@router.callback_query(F.data.startswith(CB.CART_ADD))
async def add_to_cart_cb(callback: CallbackQuery):
    _, product_id, qty, _ = callback.data.split(":", 3)

    await add_to_cart(
        user_id=callback.from_user.id,
        product_id=int(product_id),
        quantity=int(qty)
    )

    await callback.answer("✅ Добавлено в корзину")


@router.message(Command("cart"))
async def show_cart_cmd(message: Message):
    items = await get_cart_items(message.from_user.id)

    if not items:
        await message.answer("🛒 Корзина пуста")
        return

    text = "🛒 *Ваша корзина:*\n\n"
    total = 0

    for item in items:
        subtotal = item.price * item.quantity
        total += subtotal
        text += f"• {item.product.name} × {item.quantity} = {subtotal} RSD\n"

    text += f"\n*Итого:* {total} RSD"

    await message.answer(text, reply_markup=cart_keyboard(), parse_mode="Markdown")


@router.callback_query(F.data == CB.CART_CLEAR)
async def clear_cart_cb(callback: CallbackQuery):
    await clear_cart(callback.from_user.id)
    await callback.message.edit_text("🗑 Корзина очищена")