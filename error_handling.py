"""
Обработка ошибок для Barkery Shop
"""
import logging
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable, Any

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


# ========== НОВЫЙ КОД (добавляем в конец файла) ==========

class EnhancedErrorHandler:
    """Расширенная обработка ошибок с сохранением в файлы и уведомлениями"""

    @staticmethod
    async def handle_error(
            error: Exception,
            context: str = "",
            user_id: Optional[int] = None,
            notify_user: bool = True
    ) -> str:
        """
        Универсальная обработка ошибок

        Args:
            error: Исключение
            context: Контекст ошибки (например: "order_processing", "cart_update")
            user_id: ID пользователя (если есть)
            notify_user: Возвращать ли сообщение пользователю

        Returns:
            Сообщение для пользователя или пустая строка
        """
        try:
            # Генерируем ID ошибки
            error_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Сохраняем детали ошибки
            await EnhancedErrorHandler._save_error_details(
                error=error,
                context=context,
                user_id=user_id,
                error_id=error_id
            )

            # Уведомляем админа о критических ошибках
            if EnhancedErrorHandler._is_critical_error(error):
                await EnhancedErrorHandler._notify_admin(
                    error=error,
                    context=context,
                    user_id=user_id,
                    error_id=error_id
                )

            # Логируем
            logger.error(f"Ошибка в {context}: {error}")

            # Возвращаем сообщение пользователю если нужно
            if notify_user:
                return EnhancedErrorHandler._get_user_friendly_message(
                    error,
                    error_id
                )

            return ""

        except Exception as e:
            # Если сама обработка ошибок сломалась
            logger.error(f"Ошибка в обработчике ошибок: {e}")
            return "❌ Произошла внутренняя ошибка. Попробуйте позже."

    @staticmethod
    async def _save_error_details(
            error: Exception,
            context: str,
            user_id: Optional[int],
            error_id: str
    ) -> Dict:
        """Сохранение деталей ошибки в JSON файл"""
        try:
            error_details = {
                "error_id": error_id,
                "timestamp": datetime.now().isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "user_id": user_id,
                "traceback": traceback.format_exc(),
                "handled": True
            }

            # Создаем директорию для ошибок если её нет
            errors_dir = Path("logs/errors")
            errors_dir.mkdir(parents=True, exist_ok=True)

            # Сохраняем в JSON файл
            error_file = errors_dir / f"error_{error_id}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_details, f, indent=2, ensure_ascii=False, default=str)

            logger.debug(f"Детали ошибки сохранены: {error_file}")

            return {"success": True, "error_id": error_id, "file": str(error_file)}

        except Exception as e:
            logger.error(f"Не удалось сохранить детали ошибки: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _is_critical_error(error: Exception) -> bool:
        """Определяем является ли ошибка критической"""
        error_str = str(error).lower()

        # Список ключевых слов для критических ошибок
        critical_keywords = [
            "database", "база данных",
            "backup", "бекап",
            "order", "заказ",
            "payment", "оплата",
            "connection", "соединение",
            "integrity", "целостность",
            "sqlite", "sql",
            "corrupted", "поврежден"
        ]

        # Проверяем содержит ли ошибка критические ключевые слова
        for keyword in critical_keywords:
            if keyword in error_str:
                return True

        return False

    @staticmethod
    async def _notify_admin(
            error: Exception,
            context: str,
            user_id: Optional[int],
            error_id: str
    ):
        """Отправка уведомления администратору о критической ошибке"""
        try:
            from config import settings

            if not settings.admin_id or settings.admin_id == 123456789:
                logger.debug(f"Админ ID не настроен, пропускаем уведомление")
                return

            # Формируем сообщение для админа
            from datetime import datetime
            error_message = str(error)[:200]  # Берем первые 200 символов

            admin_message = (
                f"🚨 <b>КРИТИЧЕСКАЯ ОШИБКА #{error_id}</b>\n\n"
                f"📝 <b>Тип:</b> {type(error).__name__}\n"
                f"📋 <b>Контекст:</b> {context}\n"
                f"👤 <b>Пользователь:</b> {user_id or 'Неизвестно'}\n"
                f"⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
                f"<code>{error_message}...</code>"
            )

            # Временное решение - сохраняем уведомление в файл
            notifications_dir = Path("logs/admin_notifications")
            notifications_dir.mkdir(parents=True, exist_ok=True)

            notification_file = notifications_dir / f"error_{error_id}.txt"
            with open(notification_file, 'w', encoding='utf-8') as f:
                f.write(admin_message)

            logger.critical(
                f"КРИТИЧЕСКАЯ ОШИБКА #{error_id} | "
                f"Контекст: {context} | "
                f"Пользователь: {user_id} | "
                f"Ошибка: {error_message} | "
                f"Файл: {notification_file}"
            )

        except Exception as e:
            logger.error(f"Не удалось обработать уведомление админу: {e}")

    @staticmethod
    def _get_user_friendly_message(error: Exception, error_id: str) -> str:
        """Получение понятного сообщения для пользователя"""
        error_str = str(error).lower()

        # Сопоставляем ошибки с понятными сообщениями
        error_mapping = {
            "недостаточно": "❌ Недостаточно товара на складе. Пожалуйста, уменьшите количество.",
            "stock": "❌ Недостаточно товара на складе. Пожалуйста, уменьшите количество.",
            "база данных": "❌ Временная проблема с системой. Попробуйте позже.",
            "database": "❌ Временная проблема с системой. Попробуйте позже.",
            "цена": "❌ Ошибка при расчете цены. Обновите страницу.",
            "price": "❌ Ошибка при расчете цены. Обновите страницу.",
            "корзина": "❌ Проблема с корзиной. Очистите корзину и попробуйте снова.",
            "cart": "❌ Проблема с корзиной. Очистите корзину и попробуйте снова.",
            "заказ": "❌ Ошибка при оформлении заказа. Попробуйте позже.",
            "order": "❌ Ошибка при оформлении заказа. Попробуйте позже."
        }

        # Ищем подходящее сообщение
        for keyword, message in error_mapping.items():
            if keyword in error_str:
                return message

        # Если не нашли подходящее - общее сообщение
        return f"❌ Произошла ошибка (ID: {error_id}). Мы уже работаем над исправлением."

    @staticmethod
    def error_handler_decorator(context: str = ""):
        """
        Декоратор для автоматической обработки ошибок в функциях

        Использование:
            @EnhancedErrorHandler.error_handler_decorator("обработка заказа")
            async def process_order():
                ...
        """

        def decorator(func: Callable) -> Callable:
            async def async_wrapper(*args, **kwargs):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    # Определяем user_id из аргументов если возможно
                    user_id = None
                    if args and hasattr(args[0], 'from_user'):
                        user_id = args[0].from_user.id
                    elif 'callback' in kwargs:
                        user_id = kwargs['callback'].from_user.id
                    elif 'message' in kwargs:
                        user_id = kwargs['message'].from_user.id

                    # Обрабатываем ошибку
                    error_message = await EnhancedErrorHandler.handle_error(
                        error=e,
                        context=context or func.__name__,
                        user_id=user_id,
                        notify_user=False
                    )

                    # Пробрасываем ошибку дальше (можно заменить на return error_message)
                    raise

            def sync_wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    user_id = None
                    if args and hasattr(args[0], 'from_user'):
                        user_id = args[0].from_user.id

                    # Для синхронных функций просто логируем
                    logger.error(f"Ошибка в {context}: {e}")
                    raise

            # Возвращаем правильную обертку
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


# Создаем экземпляр расширенного обработчика
enhanced_error_handler = EnhancedErrorHandler()

# ========== ВСПОМОГАТЕЛЬНЫЕ ИМПОРТЫ ==========

# Импортируем asyncio для проверки async функций
import asyncio


# ========== ФУНКЦИИ ДЛЯ ОБРАТНОЙ СОВМЕСТИМОСТИ ==========

async def handle_error_gracefully(
        error: Exception,
        context: str = "",
        user_id: Optional[int] = None
) -> str:
    """
    Функция для обратной совместимости
    Обрабатывает ошибку и возвращает сообщение для пользователя
    """
    return await enhanced_error_handler.handle_error(
        error=error,
        context=context,
        user_id=user_id,
        notify_user=True
    )


# ========== ИНТЕГРАЦИЯ С СУЩЕСТВУЮЩИМ OrderErrorHandler ==========

# Расширяем существующий OrderErrorHandler для использования новых возможностей
async def handle_order_error_enhanced(self, error: Exception, user_id: int = None):
    """Расширенная обработка ошибок заказов"""
    return await enhanced_error_handler.handle_error(
        error=error,
        context="order_processing",
        user_id=user_id,
        notify_user=True
    )

# Добавляем метод к классу
OrderErrorHandler.handle_order_error_enhanced = handle_order_error_enhanced


# Альтернативно можно заменить существующий метод (если уверены)
# OrderErrorHandler.handle_order_error = lambda self, error, user_id=None: (
#     enhanced_error_handler.handle_error(
#         error=error,
#         context="order_processing",
#         user_id=user_id,
#         notify_user=True
#     )
# )