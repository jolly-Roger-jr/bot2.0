# app/utils/image_handler.py
"""
Утилиты для работы с изображениями товаров
"""

import os
import uuid
from pathlib import Path
from aiogram import Bot
from aiogram.types import PhotoSize


class ImageHandler:
    """Обработчик изображений товаров"""

    def __init__(self, base_path: str = "product_images"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    async def save_telegram_photo(self, bot: Bot, photo: PhotoSize) -> str:
        """
        Сохранить фото из Telegram
        Возвращает file_id для дальнейшего использования
        """
        # В Telegram можно использовать file_id для отправки
        # Для хранения файлов локально нужно их скачивать
        file_info = await bot.get_file(photo.file_id)

        # Можно сохранить file_id (простой способ)
        return photo.file_id

        # Альтернатива: скачать файл и сохранить локально
        # file_path = self.base_path / f"{uuid.uuid4()}.jpg"
        # await bot.download_file(file_info.file_path, file_path)
        # return str(file_path)

    def get_image_url(self, image_ref: str) -> str:
        """
        Получить URL или путь к изображению
        """
        if not image_ref:
            return ""

        if image_ref.startswith(('http://', 'https://')):
            return image_ref  # Это URL

        if os.path.exists(image_ref):
            return image_ref  # Это локальный путь

        # Предполагаем, что это file_id от Telegram
        return image_ref

    def delete_image(self, image_ref: str) -> bool:
        """
        Удалить изображение
        """
        if not image_ref:
            return True

        # Удаляем только локальные файлы
        if (image_ref.startswith(('http://', 'https://')) or
                len(image_ref) < 100):  # file_id обычно длинный
            return True

        try:
            if os.path.exists(image_ref):
                os.remove(image_ref)
            return True
        except:
            return False

    def cleanup_old_images(self, days_old: int = 30):
        """
        Очистка старых изображений
        """
        import time
        current_time = time.time()

        for file_path in self.base_path.glob("*.*"):
            file_age = current_time - os.path.getmtime(file_path)

            if file_age > days_old * 24 * 3600:
                try:
                    file_path.unlink()
                except:
                    pass


# Глобальный экземпляр
image_handler = ImageHandler()