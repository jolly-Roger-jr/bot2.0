# app/services/stock.py
from sqlalchemy import select, update
from app.db.session import get_session
from app.db.models import Product


class StockService:
    @staticmethod
    async def get_product_stock(product_id: int):
        """Получить информацию об остатках товара"""
        async for session in get_session():
            product = await session.get(Product, product_id)
            if product:
                return {
                    'id': product.id,
                    'name': product.name,
                    'available': product.available,
                    'stock_grams': product.stock_grams,
                    'price': product.price,
                    'category': product.category.name if product.category else None
                }
            return None

    @staticmethod
    async def update_stock(product_id: int, stock_grams: int, available: bool = None):
        """Обновить остатки товара"""
        async for session in get_session():
            product = await session.get(Product, product_id)
            if not product:
                return False

            product.stock_grams = max(0, stock_grams)

            if available is not None:
                product.available = available
            elif stock_grams <= 0:
                product.available = False

            await session.commit()
            return True

    @staticmethod
    async def set_availability(product_id: int, available: bool):
        """Включить/выключить товар"""
        async for session in get_session():
            await session.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(available=available)
            )
            await session.commit()
            return True

    @staticmethod
    async def add_stock(product_id: int, grams_to_add: int):
        """Добавить остатки товара"""
        async for session in get_session():
            product = await session.get(Product, product_id)
            if not product:
                return False

            new_stock = product.stock_grams + grams_to_add
            product.stock_grams = max(0, new_stock)

            if product.stock_grams > 0 and not product.available:
                product.available = True

            await session.commit()
            return True

    @staticmethod
    async def subtract_stock(product_id: int, grams_to_subtract: int):
        """Уменьшить остатки товара"""
        return await StockService.add_stock(product_id, -grams_to_subtract)

    @staticmethod
    async def get_low_stock_products(threshold: int = 1000):
        """Получить товары с низкими остатками"""
        async for session in get_session():
            result = await session.execute(
                select(Product)
                .where(Product.stock_grams > 0)
                .where(Product.stock_grams < threshold)
                .where(Product.available == True)
                .order_by(Product.stock_grams)
            )
            return result.scalars().all()

    @staticmethod
    async def get_out_of_stock_products():
        """Получить товары без остатков"""
        async for session in get_session():
            result = await session.execute(
                select(Product)
                .where(Product.stock_grams <= 0)
                .order_by(Product.name)
            )
            return result.scalars().all()


stock_service = StockService()