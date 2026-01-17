from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.services.cart import get_cart_items, clear_cart
from app.keyboards.user import confirm_keyboard

router = Router()


class Checkout(StatesGroup):
    waiting_address = State()
    confirmation = State()


@router.callback_query(F.data == "cart:checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    cart = await get_cart_items(str(callback.from_user.id))
    if not cart:
        await callback.answer("Корзина пуста", show_alert=True)
        return

    await state.set_state(Checkout.waiting_address)
    await callback.message.answer("📦 Введите адрес доставки:")
    await callback.answer()


@router.message(Checkout.waiting_address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)

    cart = await get_cart_items(str(message.from_user.id))
    total = sum(item["total"] for item in cart)

    lines = ["🧾 <b>Подтверждение заказа</b>\n"]
    for item in cart:
        lines.append(f"{item['name']} × {item['qty']}")

    lines.append(f"\n📍 Адрес: {message.text}")
    lines.append(f"\n💰 Итого: {int(total)} RSD")

    await state.set_state(Checkout.confirmation)
    await message.answer("\n".join(lines), reply_markup=confirm_keyboard())


@router.callback_query(Checkout.confirmation, F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    await clear_cart(str(callback.from_user.id))
    await state.clear()
    await callback.message.answer("✅ Заказ оформлен! Мы скоро свяжемся с вами.")
    await callback.answer()


@router.callback_query(Checkout.confirmation, F.data == "order:cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Заказ отменён")
    await callback.answer()