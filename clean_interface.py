"""
Модуль для чистого интерфейса без потери функционала.
Только управление сообщениями, без изменений логики.
"""
import logging
from typing import Dict, Optional, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


class CleanInterface:
    """
    Решает проблему артефактов в интерфейсе.
    Сохраняет ВЕСЬ существующий функционал.
    """

    def __init__(self):
        # Храним ID последнего фото-сообщения для каждого пользователя
        self.last_photo_message: Dict[int, int] = {}
        # Храним ID последнего текстового сообщения
        self.last_text_message: Dict[int, int] = {}

    async def smart_show_product(
            self,
            callback: CallbackQuery,
            text: str,
            keyboard: InlineKeyboardMarkup,
            photo_url: Optional[str] = None
    ) -> None:
        """
        Умный показ товара.
        """
        user_id = callback.from_user.id

        if photo_url:
            # Товар с фото
            # 1. Удаляем предыдущее фото если было
            await self._safe_delete_photo(user_id, callback.bot)

            # 2. Отправляем новое фото
            msg = await callback.bot.send_photo(
                chat_id=user_id,
                photo=photo_url,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            # 3. Сохраняем ID фото-сообщения
            self.last_photo_message[user_id] = msg.message_id

            # 4. Удаляем предыдущее текстовое сообщение если было
            if user_id in self.last_text_message:
                try:
                    await callback.bot.delete_message(
                        chat_id=user_id,
                        message_id=self.last_text_message[user_id]
                    )
                except:
                    pass
                finally:
                    self.last_text_message.pop(user_id, None)

        else:
            # Товар без фото
            # 1. Удаляем предыдущее фото если было
            await self._safe_delete_photo(user_id, callback.bot)

            # 2. Пробуем отредактировать текущее сообщение
            try:
                if callback.message.photo:
                    # Если текущее сообщение с фото - отправляем новое текстовое
                    msg = await callback.bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    self.last_text_message[user_id] = msg.message_id

                    # Пробуем удалить старое фото
                    try:
                        await callback.message.delete()
                    except:
                        pass

                else:
                    # Редактируем текстовое сообщение
                    await callback.message.edit_text(
                        text=text,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    self.last_text_message[user_id] = callback.message.message_id

            except TelegramBadRequest:
                # Если не удалось редактировать
                msg = await callback.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                self.last_text_message[user_id] = msg.message_id

    async def clean_navigation(
            self,
            user_id: int,
            bot,
            delete_photo: bool = True,
            delete_text: bool = False
    ) -> None:
        """
        Очистка при навигации.
        Вызывается при переходе ОТ карточки товара.
        """
        if delete_photo and user_id in self.last_photo_message:
            try:
                await bot.delete_message(
                    chat_id=user_id,
                    message_id=self.last_photo_message[user_id]
                )
            except TelegramBadRequest as e:
                if "message to delete not found" not in str(e).lower():
                    logger.debug(f"Не удалось удалить фото: {e}")
            finally:
                self.last_photo_message.pop(user_id, None)

        if delete_text and user_id in self.last_text_message:
            try:
                await bot.delete_message(
                    chat_id=user_id,
                    message_id=self.last_text_message[user_id]
                )
            except TelegramBadRequest as e:
                if "message to delete not found" not in str(e).lower():
                    logger.debug(f"Не удалось удалить текст: {e}")
            finally:
                self.last_text_message.pop(user_id, None)

    async def safe_edit_or_send(
            self,
            callback: CallbackQuery,
            text: str,
            keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """
        Безопасное редактирование или отправка сообщения.
        """
        user_id = callback.from_user.id

        # Удаляем фото если было
        await self._safe_delete_photo(user_id, callback.bot)

        try:
            # Пробуем отредактировать
            if callback.message.photo:
                # Если текущее сообщение с фото - отправляем новое
                msg = await callback.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                self.last_text_message[user_id] = msg.message_id

                # Пробуем удалить фото
                try:
                    await callback.message.delete()
                except:
                    pass

            else:
                # Редактируем текстовое
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                self.last_text_message[user_id] = callback.message.message_id

        except TelegramBadRequest:
            # Если не удалось редактировать
            msg = await callback.bot.send_message(
                chat_id=user_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            self.last_text_message[user_id] = msg.message_id

    async def handle_product_quantity_change(
            self,
            callback: CallbackQuery,
            text: str,
            keyboard: InlineKeyboardMarkup
    ) -> None:
        """
        Обработка изменения количества в карточке товара.
        Сохраняет фото если оно есть.
        """
        try:
            if callback.message.photo:
                await callback.message.edit_caption(
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except TelegramBadRequest:
            # Если сообщение устарело - ничего не делаем
            pass

    # В классе CleanInterface добавляем метод:

    async def safe_edit_or_send_message(
            self,
            message: Message,
            text: str,
            keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """
        Безопасное редактирование или отправка сообщения для Message объектов.
        """
        user_id = message.from_user.id

        # Удаляем фото если было
        await self._safe_delete_photo(user_id, message.bot)

        # Для Message объектов всегда отправляем новое сообщение
        msg = await message.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        self.last_text_message[user_id] = msg.message_id

    async def safe_edit_or_send_message(
            self,
            message: Message,
            text: str,
            keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> None:
        """
        Безопасное редактирование или отправка сообщения для Message объектов.
        Используется в обработчиках оформления заказа.
        """
        user_id = message.from_user.id

        # Удаляем предыдущее фото если было
        await self._safe_delete_photo(user_id, message.bot)

        # Проверяем есть ли последнее текстовое сообщение от бота
        if user_id in self.last_text_message:
            try:
                # Пробуем отредактировать последнее сообщение бота
                await message.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=self.last_text_message[user_id],
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return
            except TelegramBadRequest:
                # Если не удалось отредактировать, удаляем старое
                try:
                    await message.bot.delete_message(
                        chat_id=user_id,
                        message_id=self.last_text_message[user_id]
                    )
                except:
                    pass
                self.last_text_message.pop(user_id, None)

        # Отправляем новое сообщение
        msg = await message.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        self.last_text_message[user_id] = msg.message_id

    async def _safe_delete_photo(self, user_id: int, bot) -> bool:
        """Безопасное удаление фото-сообщения"""
        if user_id in self.last_photo_message:
            try:
                await bot.delete_message(
                    chat_id=user_id,
                    message_id=self.last_photo_message[user_id]
                )
                return True
            except TelegramBadRequest as e:
                if "message to delete not found" not in str(e).lower():
                    logger.debug(f"Не удалось удалить фото: {e}")
            except Exception as e:
                logger.debug(f"Ошибка при удалении фото: {e}")
            finally:
                self.last_photo_message.pop(user_id, None)
        return False


# Глобальный экземпляр
clean_ui = CleanInterface()