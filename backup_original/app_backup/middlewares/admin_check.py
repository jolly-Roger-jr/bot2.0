# app/middlewares/admin_check.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from app.config import settings


class AdminCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:
        # Проверяем, админ ли пользователь
        if event.from_user.id != settings.admin_id:
            # Игнорируем запрос если не админ
            if isinstance(event, Message) and event.text.startswith('/'):
                await event.answer("❌ У вас нет доступа к этой команде")
            return

        # Пропускаем дальше если админ
        return await handler(event, data)

# В app/bot.py добавляем:
# from app.middlewares.admin_check import AdminCheckMiddleware
# admin_router.message.middleware(AdminCheckMiddleware())
# admin_router.callback_query.middleware(AdminCheckMiddleware())