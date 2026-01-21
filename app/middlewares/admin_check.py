from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
import logging
import os

from app.config import settings

logger = logging.getLogger(__name__)


class AdminCheckMiddleware(BaseMiddleware):
    """Middleware для проверки прав администратора"""

    def __init__(self, test_mode: bool = False):
        super().__init__()
        self.test_mode = test_mode

    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # Режим тестирования или если админ ID не установлен - пропускаем
        if self.test_mode or os.getenv("TEST_MODE") == "1" or settings.admin_id == 0:
            logger.debug(f"Пропускаем проверку админа (режим тестирования) для user_id: {event.from_user.id}")
            return await handler(event, data)

        # Режим продакшн - проверяем админа
        user_id = event.from_user.id

        if user_id != settings.admin_id:
            logger.warning(f"Попытка доступа к админке от неавторизованного пользователя: {user_id}")

            if isinstance(event, Message):
                if event.text and event.text.startswith('/'):
                    await event.answer("❌ У вас нет доступа к этой команде")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ У вас нет доступа", show_alert=True)

            return

        # Пропускаем дальше если админ
        return await handler(event, data)


# Создаем экземпляр для тестов с автоматическим определением режима
def get_admin_middleware():
    """Получить middleware с автоматическим определением режима"""
    test_mode = os.getenv("TEST_MODE") == "1" or settings.admin_id == 0
    return AdminCheckMiddleware(test_mode=test_mode)