# app/handlers/user/order.py
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from app.callbacks import CB
from app.services.cart import get_cart_items, clear_cart, get_cart_total, validate_cart_for_order
from app.services.notifications import notify_admin_new_order
from app.keyboards.user import confirm_keyboard, back_to_cart_keyboard  # ✅ ТОЛЬКО нужные импорты
from app.db.session import get_session
from app.db.models import Order, OrderItem, Product, User

router = Router()


class OrderForm(StatesGroup):
    """Состояния для оформления заказа"""
    waiting_address = State()
    waiting_phone = State()


async def get_or_create_user(session, telegram_id: int, username: str = None, full_name: str = None) -> User:
    """Получить или создать пользователя"""
    result = await session.execute(
        select(User).where(User.telegram_id == str(telegram_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=str(telegram_id),
            username=username,
            full_name=full_name
        )
        session.add(user)
        await session.flush()

    return user



@router.callback_query(F.data == "cart:check_availability")
async def check_cart_availability(callback: CallbackQuery):
    """Проверка доступности товаров в корзине"""
    result = await validate_cart_for_order(callback.from_user.id)

    if not result['success']:
        if 'unavailable_items' in result:
            # Показываем какие товары недоступны
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


@router.message(Command("cancel"))
@router.callback_query(F.data == "order:cancel_state")
async def cancel_order_state(message: Message, state: FSMContext):
    """Отмена текущего состояния оформления заказа"""
    current_state = await state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer("❌ Оформление заказа отменено.")
    await message.answer("Вы можете вернуться в корзину командой /cart")


@router.callback_query(F.data == CB.CART_SHOW)
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа: проверка корзины"""
    items = await get_cart_items(callback.from_user.id)

    if not items:
        await callback.answer("🛒 Корзина пуста", show_alert=True)
        return

    # Проверяем доступность всех товаров
    unavailable_items = []
    for item in items:
        if not item.product or not item.product.available:
            unavailable_items.append(item.product.name if item.product else "Неизвестный товар")

    if unavailable_items:
        items_text = "\n".join(f"• {name}" for name in unavailable_items)
        await callback.message.answer(
            f"❌ Некоторые товары стали недоступны:\n{items_text}\n\n"
            f"Удалите их из корзины, чтобы продолжить оформление заказа."
        )
        await callback.answer()
        return

    # Сохраняем данные в состоянии
    await state.set_state(OrderForm.waiting_address)
    await state.update_data(items=items)

    await callback.message.answer(
        "📦 *Оформление заказа*\n\n"
        "📍 Пожалуйста, введите адрес доставки:\n"
        "<i>Для отмены введите /cancel</i>",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(OrderForm.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка ввода адреса"""
    if len(message.text.strip()) < 10:
        await message.answer("❌ Адрес слишком короткий. Пожалуйста, введите полный адрес:")
        return

    await state.update_data(address=message.text.strip())
    await state.set_state(OrderForm.waiting_phone)

    await message.answer(
        "📞 Теперь введите ваш номер телефона для связи:\n"
        "Например: +381 64 123-45-67\n\n"
        "<i>Для отмены введите /cancel</i>"
    )


@router.message(OrderForm.waiting_phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    """Обработка ввода телефона и подтверждение заказа"""
    phone = message.text.strip()

    # Простая валидация телефона
    if not any(char.isdigit() for char in phone):
        await message.answer("❌ Номер телефона должен содержать цифры. Попробуйте еще раз:")
        return

    data = await state.get_data()
    items = data.get("items", [])
    address = data.get("address", "")

    if not items or not address:
        await message.answer("❌ Ошибка оформления заказа. Начните заново.")
        await state.clear()
        return

    # Рассчитываем итоговую сумму
    total_result = await get_cart_total(message.from_user.id)
    if not total_result['success']:
        await message.answer("❌ Ошибка расчета суммы. Проверьте корзину.")
        await state.clear()
        return

    total_amount = total_result.get('total', 0)

    # Формируем текст подтверждения
    text = "🧾 <b>ПОДТВЕРЖДЕНИЕ ЗАКАЗА</b>\n\n"

    for item in items:
        if item.product:
            item_price = item.product.price * item.quantity / 100
            text += f"• {item.product.name}\n"
            text += f"  {item.quantity}г × {item.product.price} RSD/100г = {int(item_price)} RSD\n"

    text += f"\n<b>Итого:</b> {int(total_amount)} RSD"
    text += f"\n<b>Адрес:</b> {address}"
    text += f"\n<b>Телефон:</b> {phone}"

    # Сохраняем телефон и сумму в состоянии
    await state.update_data(phone=phone, total_amount=total_amount)

    await message.answer(text, parse_mode="HTML", reply_markup=confirm_keyboard())


@router.callback_query(F.data == CB.ORDER_CONFIRM)
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждение и сохранение заказа"""
    data = await state.get_data()
    items = data.get("items", [])
    address = data.get("address", "")
    phone = data.get("phone", "")
    total_amount = data.get("total_amount", 0)

    if not items or not address or not phone:
        await callback.answer("❌ Данные заказа утеряны", show_alert=True)
        await state.clear()
        return

    async for session in get_session():
        try:
            # Получаем или создаем пользователя
            user = await get_or_create_user(
                session,
                telegram_id=callback.from_user.id,
                username=callback.from_user.username,
                full_name=callback.from_user.full_name
            )

            # Обновляем контактные данные пользователя
            user.phone = phone
            user.address = address

            # Создаем заказ
            order = Order(
                user_id=user.id,
                address=address,
                phone=phone,
                customer_name=callback.from_user.full_name,
                total_amount=total_amount,
                status="pending"
            )
            session.add(order)
            await session.flush()

            # Создаем элементы заказа
            for item in items:
                if item.product:
                    # Уменьшаем остатки товара
                    if item.product.stock_grams >= item.quantity:
                        item.product.stock_grams -= item.quantity
                    else:
                        item.product.stock_grams = 0

                    # Создаем запись в заказе
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item.product.id,
                        product_name=item.product.name,
                        price_per_100g=item.product.price,
                        quantity=item.quantity
                    )
                    session.add(order_item)

            await session.commit()

            # Очищаем корзину
            await clear_cart(callback.from_user.id)

            # Формируем данные для уведомления админу
            order_data = {
                'order_id': order.id,
                'user_info': {
                    'id': callback.from_user.id,
                    'name': callback.from_user.full_name,
                    'username': callback.from_user.username
                },
                'items': items,
                'total': total_amount,
                'address': address,
                'phone': phone
            }

            # Отправляем уведомление админу
            await notify_admin_new_order(bot, order_data)

            # Сообщение пользователю
            await callback.message.answer(
                "✅ <b>Заказ успешно оформлен!</b>\n\n"
                f"Номер вашего заказа: <b>#{order.id}</b>\n"
                "Мы свяжемся с вами в ближайшее время для подтверждения.\n\n"
                "Спасибо за покупку! 🐾",
                parse_mode="HTML"
            )

            await callback.answer()

        except Exception as e:
            await session.rollback()
            await callback.message.answer(
                "❌ Произошла ошибка при оформлении заказа. "
                "Пожалуйста, попробуйте позже."
            )
            print(f"Order creation error: {e}")
        finally:
            await state.clear()


@router.callback_query(F.data == CB.ORDER_CANCEL)
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()

    items = await get_cart_items(callback.from_user.id)
    if items:
        await callback.message.answer(
            "❌ Оформление заказа отменено.\n"
            "Ваша корзина сохранена.",
            reply_markup=back_to_cart_keyboard()
        )
    else:
        await callback.message.answer("❌ Оформление заказа отменено.")

    await callback.answer()