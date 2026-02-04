from sqlalchemy import func
"""
"""
import asyncio
from collections import defaultdict
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import User, Product, Category, CartItem, Order, OrderItem, get_session


class CartService:
    """Сервис корзины с улучшенной защитой от race condition"""
    
    def __init__(self):
        # Блокировка на уровне пользователя+товар для более точного контроля
        self._locks = defaultdict(asyncio.Lock)
    
    def _get_lock_key(self, user_id: int, product_id: int = None) -> str:
        """Ключ для блокировки"""
        if product_id:
            return f"user:{user_id}:product:{product_id}"
        return f"user:{user_id}"
    
    async def get_or_create_user(self, telegram_id: int, username: str = "", full_name: str = "") -> User:
        """Получить или создать пользователя"""
        async with get_session() as session:
            stmt = select(User).where(User.telegram_id == str(telegram_id))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    telegram_id=str(telegram_id),
                    username=username,
                    full_name=full_name
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
            
            return user
    
    async def add_to_cart(self, user_id: int, product_id: int, quantity: int) -> Dict:
        """Добавить товар в корзину с улучшенной блокировкой"""
        lock_key = self._get_lock_key(user_id, product_id)
        lock = self._locks[lock_key]
        
        async with lock:
            async with get_session() as session:
                # Проверяем товар
                product = await session.get(Product, product_id)
                if not product or not product.available:
                    return {"success": False, "error": "Товар недоступен"}
                
                # Проверка наличия с учетом типа товара
                if product.unit_type == 'grams':
                    stock = product.stock_grams
                    unit_text = 'г'
                else:  # pieces
                    stock = product.stock_grams  # для штучных товаров хранится количество
                    unit_text = 'шт'
                
                if quantity > stock:
                    return {"success": False, "error": f"Недостаточно товара. Доступно: {stock}{unit_text}"}
                
                # Находим существующий элемент корзины
                stmt = select(CartItem).where(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
                result = await session.execute(stmt)
                cart_item = result.scalar_one_or_none()
                
                if cart_item:
                    cart_item.quantity = quantity
                else:
                    cart_item = CartItem(
                        user_id=user_id,
                        product_id=product_id,
                        quantity=quantity
                    )
                    session.add(cart_item)
                
                await session.commit()
                
                return {
                    "success": True,
                    "message": f"{product.name} добавлен в корзину ({quantity}г)",
                    "product_name": product.name,
                    "quantity": quantity
                }
    
    async def update_cart_quantity(self, user_id: int, product_id: int, delta: int) -> Dict:
        """Обновить количество товара в корзине (для +/- кнопок)"""
        lock_key = self._get_lock_key(user_id, product_id)
        lock = self._locks[lock_key]
        
        async with lock:
            async with get_session() as session:
                # Находим элемент корзины
                stmt = select(CartItem).where(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id
                )
                result = await session.execute(stmt)
                cart_item = result.scalar_one_or_none()
                
                if cart_item:
                    new_quantity = cart_item.quantity + delta
                    if new_quantity < 0:
                        new_quantity = 0
                    
                    # Проверяем товар
                    product = await session.get(Product, product_id)
                    if product and new_quantity > product.stock_grams:
                        return {
                            "success": False,
                            "error": f"Максимально доступно: {product.stock_grams}" + ("г" if product.unit_type == "grams" else "шт"),
                            "max_quantity": product.stock_grams
                        }
                    
                    cart_item.quantity = new_quantity
                    await session.commit()
                    
                    return {
                        "success": True,
                        "quantity": new_quantity,
                        "message": f"Количество обновлено: {new_quantity}г"
                    }
                else:
                    # Если товара нет в корзине, но пытаемся добавить
                    if delta > 0:
                        return await self.add_to_cart(user_id, product_id, delta)
                    else:
                        return {"success": True, "quantity": 0, "message": "Товара нет в корзине"}
    
    async def get_cart(self, user_id: int) -> Dict:
        """Получить содержимое корзины"""
        async with get_session() as session:
            stmt = select(CartItem, Product).join(
                Product, CartItem.product_id == Product.id
            ).where(CartItem.user_id == user_id)
            
            result = await session.execute(stmt)
            items = result.all()
            
            cart_items = []
            total_price = 0.0
            
            for cart_item, product in items:
                # Расчет цены в зависимости от типа товара
                if product.unit_type == 'grams':
                    item_price = (product.price / 100) * cart_item.quantity
                else:  # pieces
                    item_price = product.price * cart_item.quantity
                total_price += item_price
                
                cart_items.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "quantity": cart_item.quantity,
                    "unit_type": product.unit_type,
                    "total_price": item_price,
                    "price_per_100g": product.price
                })
            
            return {
                "success": True,
                "items": cart_items,
                "total_price": total_price,
                "total_items": len(cart_items)
            }
    
    async def clear_cart(self, user_id: int) -> Dict:
        """Очистить корзину"""
        lock_key = self._get_lock_key(user_id)
        lock = self._locks[lock_key]
        
        async with lock:
            async with get_session() as session:
                stmt = select(CartItem).where(CartItem.user_id == user_id)
                result = await session.execute(stmt)
                items = result.scalars().all()
                
                for item in items:
                    await session.delete(item)
                
                await session.commit()
                
                return {"success": True, "message": "Корзина очищена", "removed_items": len(items)}


class CatalogService:
    """Сервис каталога"""
    
    async def get_categories(self) -> List[Dict]:
        """Получить все категории"""
        async with get_session() as session:
            stmt = select(Category).order_by(Category.name)
            result = await session.execute(stmt)
            categories = result.scalars().all()
            
            return [{"id": cat.id, "name": cat.name} for cat in categories]
    
    async def get_products_by_category(self, category_id: int) -> List[Dict]:
        """Получить товары категории"""
        async with get_session() as session:
            stmt = select(Product).where(
                Product.category_id == category_id,
                Product.available == True
            ).order_by(Product.name)
            
            result = await session.execute(stmt)
            products = result.scalars().all()
            
            return [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "stock_grams": p.stock_grams,
                    "image_url": p.image_url,
                    "available": p.available,
                    "is_active": p.is_active,
                    "unit_type": p.unit_type,
                    "measurement_step": p.measurement_step
                }
                for p in products
            ]
    
    async def get_product(self, product_id: int) -> Optional[Dict]:
        """Получить товар по ID"""
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if product:
                return {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "stock_grams": product.stock_grams,
                    "image_url": product.image_url,
                    "available": product.available,
                    "is_active": product.is_active,
                    "unit_type": product.unit_type,
                    "measurement_step": product.measurement_step,
                    "category_id": product.category_id
                }
            return None
    
    async def update_product(self, product_id: int, **kwargs) -> Dict:
        """Обновить товар"""
        async with get_session() as session:
            product = await session.get(Product, product_id)
            if not product:
                return {"success": False, "error": "Товар не найден"}
            
            # Обновляем только переданные поля
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            
            await session.commit()
            return {"success": True, "product": product}


class UserService:
    """Сервис для работы с пользователями и адресами"""
    
    async def get_user_addresses(self, user_id: int) -> List[Dict]:
        """Получить адреса пользователя"""
        async with get_session() as session:
            from database import UserAddress
            stmt = select(UserAddress).where(
                UserAddress.user_id == user_id
            ).order_by(UserAddress.is_default.desc(), UserAddress.created_at.desc())
            
            result = await session.execute(stmt)
            addresses = result.scalars().all()
            
            return [
                {
                    "id": addr.id,
                    "address": addr.address,
                    "is_active": addr.is_default,
                    "created_at": addr.created_at
                }
                for addr in addresses
            ]
    
    async def add_user_address(self, user_id: int, address: str, is_default: bool = False) -> Dict:
        """Добавить адрес пользователя"""
        async with get_session() as session:
            from database import UserAddress
            
            # Если это адрес по умолчанию, снимаем флаг с других адресов
            if is_default:
                stmt = select(UserAddress).where(
                    UserAddress.user_id == user_id,
                    UserAddress.is_default == True
                )
                result = await session.execute(stmt)
                default_addresses = result.scalars().all()
                
                for addr in default_addresses:
                    addr.is_default = False
            
            # Создаем новый адрес
            new_address = UserAddress(
                user_id=user_id,
                address=address,
                is_default=is_default
            )
            
            session.add(new_address)
            await session.commit()
            await session.refresh(new_address)
            
            return {
                "success": True,
                "address": {
                    "id": new_address.id,
                    "address": new_address.address,
                    "is_default": new_address.is_default
                }
            }
    
    async def update_user_info(self, user_id: int, pet_name: str = None, telegram_login: str = None) -> Dict:
        """Обновить информацию о пользователе"""
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return {"success": False, "error": "Пользователь не найден"}
            
            if pet_name:
                user.full_name = pet_name
            if telegram_login:
                user.username = telegram_login
            
            await session.commit()
            return {"success": True, "user": user}


# Создаем экземпляры сервисов
cart_service = CartService()
catalog_service = CatalogService()
user_service = UserService()
