# app/services/user_notifications.py - НОВЫЙ ФАЙЛ

from aiogram import Bot
from app.config import settings


class UserNotificationService:
    """Сервис для отправки уведомлений пользователям"""

    @staticmethod
    async def notify_order_status_change(
            bot: Bot,
            user_id: str,
            order_id: int,
            old_status: str,
            new_status: str,
            admin_note: str = None
    ):
        """Уведомить пользователя об изменении статуса заказа"""

        status_texts = {
            'pending': '⏳ Ожидает подтверждения',
            'confirmed': '✅ Подтвержден',
            'processing': '🚚 Готовится к отправке',
            'completed': '🎉 Завершен',
            'cancelled': '❌ Отменен'
        }

        emojis = {
            'pending': '⏳',
            'confirmed': '✅',
            'processing': '🚚',
            'completed': '🎉',
            'cancelled': '❌'
        }

        old_text = status_texts.get(old_status, old_status)
        new_text = status_texts.get(new_status, new_status)
        emoji = emojis.get(new_status, '📦')

        text = f"{emoji} <b>Статус вашего заказа изменен</b>\n\n"
        text += f"<b>Заказ №{order_id}</b>\n"
        text += f"<b>Было:</b> {old_text}\n"
        text += f"<b>Стало:</b> {new_text}\n"

        if admin_note:
            text += f"\n<b>Примечание от администратора:</b>\n{admin_note}\n"

        if new_status == 'completed':
            text += "\n🎉 <b>Спасибо за покупку! Ждем вас снова!</b>"
        elif new_status == 'cancelled':
            text += "\n😔 <b>Если у вас есть вопросы, свяжитесь с нами</b>"

        try:
            await bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
            return False

    @staticmethod
    async def notify_order_created(
            bot: Bot,
            user_id: str,
            order_id: int,
            total_amount: float
    ):
        """Уведомить пользователя о создании заказа"""
        text = (
            "🎉 <b>Заказ успешно создан!</b>\n\n"
            f"<b>Номер заказа:</b> #{order_id}\n"
            f"<b>Сумма:</b> {int(total_amount)} RSD\n\n"
            "Мы свяжемся с вами в ближайшее время для подтверждения.\n"
            "Статус заказа можно отслеживать через команду /myorders"
        )

        try:
            await bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode='HTML'
            )
            return True
        except Exception as e:
            print(f"Failed to send order confirmation: {e}")
            return False


user_notification_service = UserNotificationService()