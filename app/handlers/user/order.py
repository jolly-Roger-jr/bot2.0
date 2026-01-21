# app/handlers/user/order.py - ЧИСТОЕ ЗАВЕРШЕНИЕ ЗАКАЗА
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from app.callbacks import CB
from app.services.cart import get_cart_items, clear_cart, get_cart_total, validate_cart_for_order
from app.services.notifications import notify_admin_new_order
from app.keyboards.user import confirm_keyboard, order_success_keyboard
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


@router.callback_query(F.data == "cart:show")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    """Начало оформления заказа"""
    items = await get_cart_items(callback.from_user.id)

    if not items:
        await callback.answer("🛍️ Корзина пуста", show_alert=True)
        return

    # Проверяем доступность
    unavailable_items = []
    for item in items:
        if not item.product or not item.product.available:
            unavailable_items.append(item.product.name if item.product else "Неизвестный товар")

    if unavailable_items:
        items_text = "\n".join(f"• {name}" for name in unavailable_items)
        await callback.message.answer(
            f"❌ Некоторые товары стали недоступны:\n{items_text}\n\n"
            f"Удалите их из корзины, чтобы продолжить."
        )
        await callback.answer()
        return

    # Сохраняем данные в состоянии
    await state.set_state(OrderForm.waiting_address)
    await state.update_data(items=items)

    await callback.message.answer(
        "📋 <b>Оформление заказа</b>\n\n"
        "📍 Введите адрес доставки:\n"
        "<i>Для отмены введите /cancel</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(OrderForm.waiting_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка ввода адреса"""
    if len(message.text.strip()) < 10:
        await message.answer("❌ Адрес слишком короткий. Введите полный адрес:")
        return

    await state.update_data(address=message.text.strip())
    await state.set_state(OrderForm.waiting_phone)

    await message.answer(
        "📞 Введите ваш номер телефона для связи:\n"
        "Например: +381 64 123-45-67\n\n"
        "<i>Для отмены введите /cancel</i>"
    )


@router.message(OrderForm.waiting_phone)
async def process_phone(message: Message, state: FSMContext, bot: Bot):
    """Обработка ввода телефона и подтверждение"""
    phone = message.text.strip()

    # Простая валидация
    if not any(char.isdigit() for char in phone):
        await message.answer("❌ Номер телефона должен содержать цифры:")
        return

    data = await state.get_data()
    items = data.get("items", [])
    address = data.get("address", "")

    if not items or not address:
        await message.answer("❌ Ошибка. Начните заново.")
        await state.clear()
        return

    # Рассчитываем сумму
    total_result = await get_cart_total(message.from_user.id)
    if not total_result['success']:
        await message.answer("❌ Ошибка расчета.")
        await state.clear()
        return

    total_amount = total_result.get('total', 0)

    # Формируем подтверждение
    text = "🧾 <b>ПОДТВЕРЖДЕНИЕ ЗАКАЗА</b>\n\n"

    for item in items:
        if item.product:
            item_price = item.product.price * item.quantity / 100
            text += f"• {item.product.name}\n"
            text += f"  {item.quantity}г × {item.product.price} RSD = {int(item_price)} RSD\n"

    text += f"\n<b>Итого:</b> {int(total_amount)} RSD"
    text += f"\n<b>Адрес:</b> {address}"
    text += f"\n<b>Телефон:</b> {phone}"

    # Сохраняем данные
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
        await callback.answer("❌ Данные утеряны", show_alert=True)
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

            # Обновляем контактные данные
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

            # Создаем элементы заказа и уменьшаем остатки
            order_items_text = ""
            for item in items:
                if item.product:
                    # Уменьшаем остатки
                    if item.product.stock_grams >= item.quantity:
                        item.product.stock_grams -= item.quantity
                    else:
                        item.product.stock_grams = 0

                    # Запись в заказ
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item.product.id,
                        product_name=item.product.name,
                        price_per_100g=item.product.price,
                        quantity=item.quantity
                    )
                    session.add(order_item)

                    # Формируем текст для уведомления
                    item_total = item.product.price * item.quantity / 100
                    order_items_text += f"• {item.product.name}: {item.quantity}г × {item.product.price} RSD = {int(item_total)} RSD\n"

            await session.commit()

            # Очищаем корзину
            await clear_cart(callback.from_user.id)

            # 🔥 ОТПРАВЛЯЕМ УВЕДОМЛЕНИЕ АДМИНУ
            admin_notification = (
                f"🆕 <b>НОВЫЙ ЗАКАЗ #{order.id}</b>\n\n"
                f"👤 <b>Покупатель:</b>\n"
                f"• Имя: {callback.from_user.full_name}\n"
                f"• Телефон: {phone}\n"
                f"• Адрес: {address}\n\n"
                f"📦 <b>Товары:</b>\n{order_items_text}\n"
                f"💰 <b>Итого:</b> {int(total_amount)} RSD"
            )

            from app.config import settings
            try:
                await bot.send_message(
                    chat_id=settings.admin_id,
                    text=admin_notification,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления админа: {e}")

            # 🔥 ОЧИЩАЕМ ЧАТ И ПОКАЗЫВАЕМ ТОЛЬКО ИТОГ
            try:
                await callback.message.delete()
            except:
                pass

            # Отправляем финальное сообщение пользователю
            final_text = (
                f"🎉 <b>ЗАКАЗ #{order.id} ОФОРМЛЕН!</b>\n\n"
                f"<b>Ваш заказ:</b>\n{order_items_text}\n"
                f"<b>Итого к оплате:</b> {int(total_amount)} RSD\n\n"
                f"<b>Детали доставки:</b>\n"
                f"📍 Адрес: {address}\n"
                f"📞 Телефон: {phone}\n\n"
                f"Мы свяжемся с вами для подтверждения.\n"
                f"Спасибо за покупку! 🐕‍🦺"
            )

            await callback.message.answer(
                final_text,
                parse_mode="HTML",
                reply_markup=order_success_keyboard()
            )

            await callback.answer()

        except Exception as e:
            await session.rollback()
            await callback.message.answer(
                "❌ Произошла ошибка. Попробуйте позже."
            )
            logger.error(f"Order creation error: {e}")
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


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """Команда отмены"""
    await state.clear()
    await message.answer("❌ Текущее действие отменено.")