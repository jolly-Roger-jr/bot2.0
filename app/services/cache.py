# app/services/cache.py
import asyncio
from typing import Optional


class CacheService:
    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()

    async def get_categories(self) -> Optional[list]:
        async with self._lock:
            return self._cache.get('categories')

    async def set_categories(self, categories: list, ttl: int = 300):
        async with self._lock:
            self._cache['categories'] = {
                'data': categories,
                'expires': asyncio.get_event_loop().time() + ttl
            }