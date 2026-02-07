"""
УЛЬТРА-БЫСТРЫЙ сервис для работы с количеством товаров
Цель: 10-30 мс на обработку кнопки +/-
"""
import asyncio
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class QuantityService:
    """Сервис для быстрой работы с количеством товаров"""

    def __init__(self):
        # Кэши в памяти
        self._user_cache: Dict[str, Dict] = {}  # telegram_id -> user_data
        self._product_cache: Dict[int, Dict] = {}  # product_id -> product_data
        self._cart_cache: Dict[str, Dict[int, int]] = {}  # user_id -> {product_id: quantity}
        self._temp_cache: Dict[str, int] = {}  # user_id:product_id -> temp_quantity

        # Время жизни кэша (5 минут)
        self._cache_ttl = 300

        # Блокировки для потокобезопасности
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock = asyncio.Lock()

        # Статистика
        self._stats = {
            'user_cache_hits': 0,
            'user_cache_misses': 0,
            'product_cache_hits': 0,
            'product_cache_misses': 0
        }

        logger.info("✅ QuantityService инициализирован")

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Получить блокировку для ключа"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get_user_fast(self, telegram_id: int) -> Optional[Dict]:
        """Быстро получить пользователя из кэша или БД"""
        user_key = f"user:{telegram_id}"

        # Проверяем кэш
        if user_key in self._user_cache:
            cached = self._user_cache[user_key]
            if time.time() - cached['timestamp'] < self._cache_ttl:
                self._stats['user_cache_hits'] += 1
                return cached['data']

        # Не в кэше - загружаем из БД
        self._stats['user_cache_misses'] += 1

        try:
            from database import get_session, User
            from sqlalchemy import select

            async with get_session() as session:
                stmt = select(User).where(User.telegram_id == str(telegram_id))
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user:
                    user_data = {
                        'id': user.id,
                        'telegram_id': user.telegram_id,
                        'username': user.telegram_username,
                        'pet_name': user.pet_name,
                        'full_name': user.full_name
                    }

                    # Сохраняем в кэш
                    self._user_cache[user_key] = {
                        'data': user_data,
                        'timestamp': time.time()
                    }

                    return user_data

                return None

        except Exception as e:
            logger.error(f"Ошибка загрузки пользователя {telegram_id}: {e}")
            return None

    async def get_product_fast(self, product_id: int) -> Optional[Dict]:
        """Быстро получить товар из кэша или БД"""
        # Проверяем кэш
        if product_id in self._product_cache:
            cached = self._product_cache[product_id]
            if time.time() - cached['timestamp'] < self._cache_ttl:
                self._stats['product_cache_hits'] += 1
                return cached['data']

        # Не в кэше - загружаем из БД
        self._stats['product_cache_misses'] += 1

        try:
            from database import get_session, Product
            from sqlalchemy import select

            async with get_session() as session:
                product = await session.get(Product, product_id)

                if product:
                    product_data = {
                        'id': product.id,
                        'name': product.name,
                        'description': product.description,
                        'price': product.price,
                        'stock_grams': product.stock_grams,
                        'image_url': product.image_url,
                        'available': product.available,
                        'unit_type': product.unit_type,
                        'measurement_step': product.measurement_step,
                        'category_id': product.category_id
                    }

                    # Сохраняем в кэш
                    self._product_cache[product_id] = {
                        'data': product_data,
                        'timestamp': time.time()
                    }

                    return product_data

                return None

        except Exception as e:
            logger.error(f"Ошибка загрузки товара {product_id}: {e}")
            return None

    async def get_cart_quantity_fast(self, user_id: int, product_id: int) -> int:
        """Быстро получить количество товара в корзине"""
        cart_key = f"cart:{user_id}"

        # Проверяем кэш корзины
        if cart_key in self._cart_cache:
            return self._cart_cache[cart_key].get(product_id, 0)

        # Если кэша нет, загружаем корзину один раз
        try:
            from database import get_session, CartItem
            from sqlalchemy import select

            async with get_session() as session:
                stmt = select(CartItem).where(CartItem.user_id == user_id)
                result = await session.execute(stmt)
                cart_items = result.scalars().all()

                # Создаем словарь для быстрого доступа
                cart_dict = {}
                for item in cart_items:
                    cart_dict[item.product_id] = item.quantity

                # Сохраняем в кэш
                self._cart_cache[cart_key] = cart_dict

                return cart_dict.get(product_id, 0)

        except Exception as e:
            logger.error(f"Ошибка загрузки корзины пользователя {user_id}: {e}")
            return 0

    async def update_temp_quantity(self, user_id: int, product_id: int, delta: int) -> Dict:
        """Обновить временное количество в памяти"""
        key = f"temp:{user_id}:{product_id}"
        lock = self._get_lock(key)

        async with lock:
            current = self._temp_cache.get(key, 0)
            new_value = current + delta

            # Не может быть меньше 0
            if new_value < 0:
                new_value = 0

            # Сохраняем
            self._temp_cache[key] = new_value

            return {
                'success': True,
                'quantity': new_value,
                'changed': delta != 0,
                'old_value': current
            }

    async def get_temp_quantity(self, user_id: int, product_id: int) -> int:
        """Получить временное количество"""
        key = f"temp:{user_id}:{product_id}"
        return self._temp_cache.get(key, 0)

    async def reset_temp_quantity(self, user_id: int, product_id: int):
        """Сбросить временное количество"""
        key = f"temp:{user_id}:{product_id}"
        if key in self._temp_cache:
            del self._temp_cache[key]
            logger.debug(f"Временное количество сброшено: {key}")

    async def invalidate_user_cache(self, telegram_id: int):
        """Инвалидировать кэш пользователя"""
        user_key = f"user:{telegram_id}"
        if user_key in self._user_cache:
            del self._user_cache[user_key]
            logger.debug(f"Кэш пользователя инвалидирован: {telegram_id}")

    async def invalidate_product_cache(self, product_id: int):
        """Инвалидировать кэш товара"""
        if product_id in self._product_cache:
            del self._product_cache[product_id]
            logger.debug(f"Кэш товара инвалидирован: {product_id}")

    async def invalidate_cart_cache(self, user_id: int):
        """Инвалидировать кэш корзины"""
        cart_key = f"cart:{user_id}"
        if cart_key in self._cart_cache:
            del self._cart_cache[cart_key]
            logger.debug(f"Кэш корзины инвалидирован: {user_id}")

    async def update_cart_cache(self, user_id: int, product_id: int, new_quantity: int):
        """Обновить кэш корзины после изменения"""
        cart_key = f"cart:{user_id}"

        if cart_key in self._cart_cache:
            self._cart_cache[cart_key][product_id] = new_quantity
        else:
            # Если кэша нет, инвалидируем чтобы загрузить заново
            await self.invalidate_cart_cache(user_id)

    async def clear_cart_cache(self, user_id: int):
        """Полностью очистить кэш корзины"""
        cart_key = f"cart:{user_id}"
        if cart_key in self._cart_cache:
            self._cart_cache[cart_key] = {}
            logger.debug(f"Кэш корзины очищен: {user_id}")

    def get_stats(self) -> Dict:
        """Получить статистику кэширования"""
        total_user = self._stats['user_cache_hits'] + self._stats['user_cache_misses']
        total_product = self._stats['product_cache_hits'] + self._stats['product_cache_misses']

        user_hit_rate = (
            self._stats['user_cache_hits'] / total_user * 100
            if total_user > 0 else 0
        )

        product_hit_rate = (
            self._stats['product_cache_hits'] / total_product * 100
            if total_product > 0 else 0
        )

        return {
            'user_cache': {
                'hits': self._stats['user_cache_hits'],
                'misses': self._stats['user_cache_misses'],
                'hit_rate': f"{user_hit_rate:.1f}%",
                'size': len(self._user_cache)
            },
            'product_cache': {
                'hits': self._stats['product_cache_hits'],
                'misses': self._stats['product_cache_misses'],
                'hit_rate': f"{product_hit_rate:.1f}%",
                'size': len(self._product_cache)
            },
            'cart_cache': {
                'size': len(self._cart_cache)
            },
            'temp_cache': {
                'size': len(self._temp_cache)
            }
        }

    async def cleanup_old_cache(self):
        """Очистить старый кэш"""
        now = time.time()
        cleaned = 0

        # Очищаем пользователей
        keys_to_remove = []
        for key, cached in self._user_cache.items():
            if now - cached['timestamp'] > self._cache_ttl:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._user_cache[key]
            cleaned += 1

        # Очищаем товары
        keys_to_remove = []
        for key, cached in self._product_cache.items():
            if now - cached['timestamp'] > self._cache_ttl:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._product_cache[key]
            cleaned += 1

        if cleaned > 0:
            logger.debug(f"Очищено {cleaned} устаревших записей кэша")

        return cleaned


# Создаем глобальный экземпляр
quantity_service = QuantityService()