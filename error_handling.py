"""
Обработка ошибок для Barkery Shop
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderErrorHandler:
    """Обработчик ошибок заказов"""
    
    @staticmethod
    async def handle_order_error(error: Exception, user_id: int = None):
        """Логирование ошибки заказа"""
        from logging_config import OperationLogger
        
        OperationLogger.log_operation(
            operation="order_error",
            user_id=user_id,
            status="error",
            error=str(error)
        )
        
        # Простое сообщение пользователю
        if "недостаточно" in str(error).lower():
            return "❌ Недостаточно товара на складе. Пожалуйста, уменьшите количество."
        else:
            return "❌ Произошла ошибка при оформлении заказа. Попробуйте позже."

# Создаем экземпляр для импорта
order_error_handler = OrderErrorHandler()
