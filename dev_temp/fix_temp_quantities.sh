#!/bin/bash
# Исправляем handlers.py

# 1. Создаем новую версию handlers.py
cat > handlers_new.py << 'PYEOF'
"""
Barkery Bot - handlers.py (исправленная версия с TTL)
ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ с обработкой изображений
Восстановлена: 2026-01-30
Обновлена: 2026-02-03 (добавлен TTL для temp_quantities)
"""
import logging
import time
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest

from keyboards import (
    main_menu_keyboard,
    categories_keyboard,
    products_keyboard,
    product_card_keyboard,
    cart_keyboard,
    order_confirmation_keyboard
)
from services import cart_service, catalog_service, user_service, update_product_stock_and_availability
from database import get_session, Product, CartItem, User
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = Router()

# Дебаунсинг для быстрых кликов
last_ui_update = {}

# ========== КЛАСС ДЛЯ УПРАВЛЕНИЯ ВРЕМЕННЫМИ КОЛИЧЕСТВАМИ С TTL ==========

class TempQuantitiesManager:
    """Менеджер временных количеств с TTL"""
    
    def __init__(self, ttl_seconds: int = 7200, max_size: int = 5000):
        self._data: dict = {}  # key -> {'value': int, 'timestamp': float}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()
    
    def _get_key(self, user_id: int, product_id: int) -> str:
        return f"{user_id}_{product_id}"
    
    def _is_expired(self, timestamp: float) -> bool:
        return time.time() - timestamp > self._ttl
    
    async def _cleanup_if_needed(self):
        current_time = time.time()
        if (current_time - self._last_cleanup > 300 or 
            len(self._data) > self._max_size * 0.9):
            await self.cleanup_expired()
            self._last_cleanup = current_time
    
    async def get(self, user_id: int, product_id: int) -> int:
        key = self._get_key(user_id, product_id)
        async with self._lock:
            if key in self._data:
                entry = self._data[key]
                if not self._is_expired(entry['timestamp']):
                    return entry['value']
                else:
                    del self._data[key]
            return 0
    
    async def set(self, user_id: int, product_id: int, value: int) -> int:
        if value < 0:
            value = 0
        key = self._get_key(user_id, product_id)
        async with self._lock:
            await self._cleanup_if_needed()
            self._data[key] = {
                'value': value,
                'timestamp': time.time()
            }
            return value
    
    async def update(self, user_id: int, product_id: int, delta: int) -> int:
        current = await self.get(user_id, product_id)
        new_value = current + delta
        if new_value < 0:
            new_value = 0
        return await self.set(user_id, product_id, new_value)
    
    async def reset(self, user_id: int, product_id: int):
        key = self._get_key(user_id, product_id)
        async with self._lock:
            if key in self._data:
                del self._data[key]
    
    async def cleanup_expired(self):
        async with self._lock:
            keys_to_remove = []
            for key, entry in self._data.items():
                if self._is_expired(entry['timestamp']):
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._data[key]
            if keys_to_remove:
                logger.debug(f"Очищено {len(keys_to_remove)} устаревших записей temp_quantities")
    
    async def cleanup_user(self, user_id: int):
        async with self._lock:
            user_prefix = f"{user_id}_"
            keys_to_remove = [
                key for key in self._data.keys() 
                if key.startswith(user_prefix)
            ]
            for key in keys_to_remove:
                del self._data[key]
            return len(keys_to_remove)

# Глобальный экземпляр
temp_quantities_manager = TempQuantitiesManager()

# Функции для обратной совместимости
async def update_temp_quantity_async(user_id: int, product_id: int, delta: int) -> int:
    """Асинхронная версия update_temp_quantity"""
    return await temp_quantities_manager.update(user_id, product_id, delta)

async def reset_temp_quantity_async(user_id: int, product_id: int):
    """Асинхронная версия reset_temp_quantity"""
    await temp_quantities_manager.reset(user_id, product_id)

def get_temp_quantity_key(user_id: int, product_id: int) -> str:
    """Ключ для хранения временного количества"""
    return f"{user_id}_{product_id}"

# ========== СОСТОЯНИЯ ДЛЯ ЗАКАЗА ==========

class OrderForm(StatesGroup):
    waiting_pet_name = State()
    waiting_address = State()
    waiting_telegram_login = State()  # Только если нет telegram_username
    waiting_address_change = State()  # Для проверки изменения адреса

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

# Синхронные обертки для совместимости (используются в колбэках)
def update_temp_quantity(user_id: int, product_id: int, delta: int) -> int:
    """Синхронная обертка для обратной совместимости"""
    import asyncio
    try:
        # Пытаемся получить текущий event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если loop работает, создаем задачу
            future = asyncio.run_coroutine_threadsafe(
                temp_quantities_manager.update(user_id, product_id, delta),
                loop
            )
            return future.result(timeout=2)
        else:
            # Если loop не работает, запускаем
            return asyncio.run(temp_quantities_manager.update(user_id, product_id, delta))
    except Exception as e:
        logger.error(f"Ошибка в update_temp_quantity: {e}")
        return 0

def reset_temp_quantity(user_id: int, product_id: int):
    """Синхронная обертка для обратной совместимости"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                temp_quantities_manager.reset(user_id, product_id),
                loop
            )
            future.result(timeout=2)
        else:
            asyncio.run(temp_quantities_manager.reset(user_id, product_id))
    except Exception as e:
        logger.error(f"Ошибка в reset_temp_quantity: {e}")

PYEOF

# 2. Добавляем остальную часть оригинального handlers.py (после строки 70)
awk 'NR > 70' handlers.py >> handlers_new.py

echo "Создан handlers_new.py"
