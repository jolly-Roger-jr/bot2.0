from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models import User, Order, OrderItem
from app.services.cart import get_cart, clear_cart
from app.services.notifications import notify_admin

router = Router()

@router.callback_query(F.data == "order")
async def create_order(call: CallbackQuery, bot):
    user_id = call.from_user.id

    async with SessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.tg_id == user_id)
        )).scalar_one_or_none()

        if not user or not user.phone:
            await call.message.answer(
                "📞 Пожалуйста, отправьте номер телефона для оформления заказа"
            )
            return

        cart = await get_cart(user_id)
        if not cart:
            await call.answer("Корзина пуста")
            return

        total = 0
        order = Order(user_id=user.id, total_price=0)
        session.add(order)
        await session.flush()

        text = "🛎️ *Новый заказ Barkery*\n\n"

        for item, product in cart:
            price = (item.grams // 100) * product.price_per_100g
            total += price

            session.add(OrderItem(
                order_id=order.id,
                product_name=product.name,
                grams=item.grams,
                price=price
            ))

            text += f"• {product.name} — {item.grams} г = {price} RSD\n"

        order.total_price = total
        await session.commit()
        await clear_cart(user_id)

    text += (
        f"\n💰 *Итого:* {total} RSD\n\n"
        f"👤 Клиент: @{call.from_user.username or '—'}\n"
        f"📞 Телефон: {user.phone}"
    )

    await notify_admin(bot, text)
    await call.message.edit_text("✅ Заказ оформлен! Мы скоро свяжемся с вами 🐾")