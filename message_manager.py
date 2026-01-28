"""
Менеджер сообщений для очистки интерфейса - исправленная версия
"""
import logging
from typing import Dict, Optional
from aiogram.types import Message
from aiogram import Bot

logger = logging.getLogger(__name__)


class MessageManager:
    """Управление сообщениями для очистки интерфейса"""
    
    def __init__(self):
        self.user_last_message: Dict[int, int] = {}
    
    async def update_last_message(self, user_id: int, message_id: int):
        """Обновить последнее сообщение пользователя"""
        self.user_last_message[user_id] = message_id
    
    async def delete_previous_message(self, bot: Bot, user_id: int):
        """Удалить предыдущее сообщение пользователя"""
        if bot is None:
            logger.warning("⚠️ Bot is None in delete_previous_message")
            return
        
        if user_id in self.user_last_message:
            try:
                await bot.delete_message(
                    chat_id=user_id,
                    message_id=self.user_last_message[user_id]
                )
                logger.debug(f"Удалено предыдущее сообщение для пользователя {user_id}")
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")
    
    async def send_with_cleanup(self, bot: Bot, chat_id: int, text: str, **kwargs) -> Optional[Message]:
        """
        Отправить сообщение с удалением предыдущего
        """
        # Проверяем bot
        if bot is None:
            logger.warning("⚠️ Bot is None in send_with_cleanup")
            return None
        
        # Удаляем предыдущее сообщение
        await self.delete_previous_message(bot, chat_id)
        
        # Отправляем новое сообщение
        try:
            msg = await bot.send_message(chat_id=chat_id, text=text, **kwargs)
            
            # Сохраняем ID нового сообщения
            await self.update_last_message(chat_id, msg.message_id)
            
            return msg
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            return None
    
    async def send_photo_with_cleanup(self, bot: Bot, chat_id: int, photo: str, caption: str, **kwargs) -> Optional[Message]:
        """
        Отправить фото с удалением предыдущего сообщения
        """
        # Проверяем bot
        if bot is None:
            logger.warning("⚠️ Bot is None in send_photo_with_cleanup")
            return None
        
        # Удаляем предыдущее сообщение
        await self.delete_previous_message(bot, chat_id)
        
        # Отправляем фото
        try:
            msg = await bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                **kwargs
            )
            
            # Сохраняем ID нового сообщения
            await self.update_last_message(chat_id, msg.message_id)
            
            return msg
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            return None


# Глобальный экземпляр
message_manager = MessageManager()
