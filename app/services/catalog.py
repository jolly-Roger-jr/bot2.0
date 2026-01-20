# app/services/catalog.py
from sqlalchemy import select
from app.db.session import get_session
from app.db.models import Category, Product


async def get_categories() -> list[str]:
    """Получить список категорий"""
    async for session in get_session():
        try:
            result = await session.execute(select(Category.name))
            categories = result.scalars().all()
            return categories if categories else []
        except Exception as e:
            print(f"❌ Ошибка при получении категорий: {e}")
            return []


async def get_products_by_category(category_name: str) -> list:
    """Получить товары по категории"""
    async for session in get_session():
        try:
            stmt = (
                select(Product)
                .join(Category)
                .where(Category.name == category_name)
            )
            result = await session.scalars(stmt)
            products = result.all()
            return products if products else []
        except Exception as e:
            print(f"❌ Ошибка при получении товаров категории '{category_name}': {e}")
            return []


async def get_product(product_id: int):
    """Получить товар по ID"""
    async for session in get_session():
        try:
            product = await session.get(Product, product_id)
            return product
        except Exception as e:
            print(f"❌ Ошибка при получении товара #{product_id}: {e}")
            return None