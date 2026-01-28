"""
Уведомления для админа
"""
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

async def notify_admin(bot, order_data: dict, order_id: int):
    """
    Отправляет уведомление админу о новом заказе
    """
    try:
        if not settings.admin_id or settings.admin_id == 123456789:
            logger.warning("⚠️ ADMIN_ID не настроен")
            return False
        
        # Форматируем сообщение
        admin_message = format_admin_notification(order_data, order_id)
        
        # Отправляем админу
        await bot.send_message(
            chat_id=settings.admin_id,
            text=admin_message,
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Уведомление отправлено админу {settings.admin_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки уведомления админу: {e}")
        return False


def format_admin_notification(order_data: dict, order_id: int) -> str:
    """Форматирует уведомление для админа"""
    
    # Формируем список товаров
    items_text = ""
    for item in order_data.get("cart_items", []):
        items_text += f"• {item['product_name']}: {item['quantity_grams']}г - {item['total_price']:.0f} RSD\n"
    
    notification = (
        f"🛎️ <b>НОВЫЙ ЗАКАЗ #{order_id}</b>\n\n"
        f"👤 <b>Покупатель:</b> {order_data.get('pet_name', 'Не указано')}\n"
        f"📱 <b>Telegram:</b> @{order_data.get('telegram_login', 'Не указан')}\n"
        f"📍 <b>Адрес доставки:</b>\n{order_data['address']}\n\n"
        f"📦 <b>Состав заказа:</b>\n{items_text}\n"
        f"💰 <b>Итого:</b> {order_data['total_amount']:.0f} RSD\n"
        f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        f"🆔 <b>User ID:</b> {order_data.get('user_id', 'Не указан')}"
    )
    
    return notification


async def send_backup_notification(bot, backup_file: str):
    """Уведомление о создании резервной копии"""
    try:
        if settings.admin_id:
            await bot.send_message(
                chat_id=settings.admin_id,
                text=f"📂 <b>Создана резервная копия БД</b>\n\nФайл: <code>{backup_file}</code>",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Ошибка уведомления о бекапе: {e}")
