# message_manager.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
import logging
from typing import Optional, Dict, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputFile
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class MessageManager:
    """
    Менеджер для управления единственным активным сообщением пользователя.
    """

    def __init__(self):
        self.active_messages: Dict[int, int] = {}
        self.last_content_type: Dict[int, str] = {}  # Храним тип последнего контента

    async def update_message(
            self,
            user_id: int,
            message_or_callback: Union[Message, CallbackQuery],
            text: str,
            keyboard: Optional[InlineKeyboardMarkup] = None,
            photo: Optional[Union[str, InputFile]] = None,
            delete_previous: bool = True
    ) -> Message:
        """Обновить или создать единственное активное сообщение"""
        bot = message_or_callback.bot

        try:
            # УДАЛЯЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ ВСЕГДА для чистоты
            if user_id in self.active_messages:
                try:
                    await bot.delete_message(
                        chat_id=user_id,
                        message_id=self.active_messages[user_id]
                    )
                except TelegramBadRequest as e:
                    if "message to delete not found" not in str(e).lower():
                        logger.warning(f"Не удалось удалить сообщение: {e}")
                except Exception as e:
                    logger.warning(f"Ошибка при удалении сообщения: {e}")

            # Определяем тип контента
            content_type = "photo" if photo else "text"
            self.last_content_type[user_id] = content_type

            # Отправляем новое сообщение
            if photo:
                msg = await bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # ВАЖНО: Если предыдущий контент был фото, а сейчас текст,
                # нужно явно отправить текстовое сообщение
                msg = await bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )

            # Сохраняем ID нового активного сообщения
            self.active_messages[user_id] = msg.message_id

            return msg

        except Exception as e:
            logger.error(f"Ошибка в update_message: {e}")
            raise

    async def safe_edit_message(
            self,
            user_id: int,
            message: Message,
            text: str,
            keyboard: Optional[InlineKeyboardMarkup] = None,
            force_new: bool = False
    ) -> bool:
        """
        Безопасное редактирование.
        force_new=True - всегда создавать новое сообщение
        """
        try:
            if force_new or self.last_content_type.get(user_id) == "photo":
                # Если последним был фото или принудительно - создаём новое
                await self.update_message(
                    user_id=user_id,
                    message_or_callback=message,
                    text=text,
                    keyboard=keyboard,
                    delete_previous=True
                )
                return False

            # Пробуем редактировать текстовое сообщение
            if message.photo:
                # Если текущее сообщение с фото, создаём новое текстовое
                await self.update_message(
                    user_id=user_id,
                    message_or_callback=message,
                    text=text,
                    keyboard=keyboard,
                    delete_previous=True
                )
                return False
            else:
                # Редактируем текстовое сообщение
                await message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                self.last_content_type[user_id] = "text"
                return True

        except TelegramBadRequest as e:
            # Если сообщение уже изменялось или устарело
            await self.update_message(
                user_id=user_id,
                message_or_callback=message,
                text=text,
                keyboard=keyboard,
                delete_previous=True
            )
            return False
        except Exception as e:
            logger.error(f"Ошибка в safe_edit_message: {e}")
            return False

    async def update_to_text(
            self,
            user_id: int,
            message: Message,
            text: str,
            keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """Явно перейти на текстовое сообщение (с удалением фото)"""
        await self.update_message(
            user_id=user_id,
            message_or_callback=message,
            text=text,
            keyboard=keyboard,
            delete_previous=True
        )


message_manager = MessageManager()