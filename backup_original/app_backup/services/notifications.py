# app/services/notifications.py - ОБНОВЛЕННЫЙ

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config import settings


async def notify_admin_new_order(bot: Bot, order_data: dict):
    """Отправить админу уведомление о новом заказе с кнопками"""

    order_id = order_data.get('order_id')
    user_info = order_data.get('user_info', {})
    items = order_data.get('items', [])
    total = order_data.get('total', 0)
    address = order_data.get('address', '')
    phone = order_data.get('phone', '')

    # Формируем текст
    text = f"🛒 <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"

    # Информация о покупателе
    text += f"<b>👤 Покупатель:</b>\n"
    text += f"• Имя: {user_info.get('name', 'Не указано')}\n"
    if user_info.get('username'):
        text += f"• @{user_info['username']}\n"
    text += f"• ID: {user_info.get('id', 'Неизвестно')}\n"
    text += f"• Телефон: {phone}\n\n"

    # Адрес
    text += f"<b>📍 Адрес доставки:</b>\n{address}\n\n"

    # Товары
    text += f"<b>📦 Товары ({len(items)}):</b>\n"
    for item in items:
        if hasattr(item, 'product') and item.product:
            item_total = item.product.price * item.quantity / 100
            text += f"• {item.product.name} - {item.quantity}г = {int(item_total)} RSD\n"

    text += f"\n<b>💰 Итого:</b> {int(total)} RSD"

    # Клавиатура с действиями
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"admin:order:confirm:{order_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"admin:order:cancel:{order_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Детали заказа",
                    callback_data=f"admin:order:view:{order_id}"
                ),
                InlineKeyboardButton(
                    text="📞 Позвонить",
                    url=f"tel:{phone}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Написать в Telegram",
                    url=f"tg://user?id={user_info.get('id')}"
                )
            ]
        ]
    )

    try:
        await bot.send_message(
            chat_id=settings.admin_id,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        return True
    except Exception as e:
        print(f"Failed to notify admin: {e}")
        return False


async def notify_admin(bot: Bot, text: str):
    """Общая функция уведомления админа"""
    try:
        await bot.send_message(
            chat_id=settings.admin_id,
            text=text,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"Failed to notify admin: {e}")
        return False