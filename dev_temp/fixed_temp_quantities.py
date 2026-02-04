"""
Исправленная система временных количеств с TTL и ограничениями
"""

import time
from typing import Dict, Optional
import asyncio

class TempQuantitiesManager:
    """Менеджер временных количеств с TTL"""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10000):
        """
        Args:
            ttl_seconds: Время жизни записей в секундах (по умолчанию 1 час)
            max_size: Максимальное количество записей (очистка старых при превышении)
        """
        self._data: Dict[str, Dict] = {}  # key -> {'value': int, 'timestamp': float}
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()
        
    def _get_key(self, user_id: int, product_id: int) -> str:
        """Генерирует ключ для хранения"""
        return f"{user_id}_{product_id}"
    
    def _is_expired(self, timestamp: float) -> bool:
        """Проверяет, истекло ли время жизни записи"""
        return time.time() - timestamp > self._ttl
    
    async def _cleanup_if_needed(self):
        """Очистка устаревших записей при необходимости"""
        current_time = time.time()
        
        # Очищаем раз в 5 минут или при превышении размера
        if (current_time - self._last_cleanup > 300 or 
            len(self._data) > self._max_size):
            await self.cleanup_expired()
            self._last_cleanup = current_time
    
    async def get(self, user_id: int, product_id: int) -> int:
        """Получить значение"""
        key = self._get_key(user_id, product_id)
        
        async with self._lock:
            if key in self._data:
                entry = self._data[key]
                if not self._is_expired(entry['timestamp']):
                    return entry['value']
                else:
                    # Удаляем просроченную запись
                    del self._data[key]
            return 0
    
    async def set(self, user_id: int, product_id: int, value: int) -> int:
        """Установить значение"""
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
        """Обновить значение на дельту"""
        current = await self.get(user_id, product_id)
        new_value = current + delta
        
        if new_value < 0:
            new_value = 0
            
        return await self.set(user_id, product_id, new_value)
    
    async def reset(self, user_id: int, product_id: int):
        """Сбросить значение"""
        key = self._get_key(user_id, product_id)
        async with self._lock:
            if key in self._data:
                del self._data[key]
    
    async def cleanup_expired(self):
        """Очистка всех устаревших записей"""
        async with self._lock:
            keys_to_remove = []
            for key, entry in self._data.items():
                if self._is_expired(entry['timestamp']):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._data[key]
            
            if keys_to_remove:
                print(f"[TempQuantitiesManager] Очищено {len(keys_to_remove)} устаревших записей")
    
    async def cleanup_user(self, user_id: int):
        """Очистить все записи пользователя"""
        async with self._lock:
            user_prefix = f"{user_id}_"
            keys_to_remove = [
                key for key in self._data.keys() 
                if key.startswith(user_prefix)
            ]
            
            for key in keys_to_remove:
                del self._data[key]
            
            return len(keys_to_remove)
    
    async def get_stats(self) -> Dict:
        """Получить статистику"""
        async with self._lock:
            await self._cleanup_if_needed()
            return {
                'total_entries': len(self._data),
                'ttl_seconds': self._ttl,
                'max_size': self._max_size
            }

# Глобальный экземпляр
temp_quantities_manager = TempQuantitiesManager()

# Функции-обертки для обратной совместимости
def get_temp_quantity_key(user_id: int, product_id: int) -> str:
    """Ключ для хранения временного количества (для обратной совместимости)"""
    return f"{user_id}_{product_id}"

async def update_temp_quantity(user_id: int, product_id: int, delta: int) -> int:
    """Обновить временное количество с проверками"""
    return await temp_quantities_manager.update(user_id, product_id, delta)

async def reset_temp_quantity(user_id: int, product_id: int):
    """Сбросить временное количество"""
    await temp_quantities_manager.reset(user_id, product_id)

async def get_temp_quantity(user_id: int, product_id: int) -> int:
    """Получить текущее временное количество"""
    return await temp_quantities_manager.get(user_id, product_id)
