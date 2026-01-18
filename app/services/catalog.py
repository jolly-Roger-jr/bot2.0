# app/services/catalog.py

from app.db.session import get_session
from app.db.models import Product, Category
from app.schemas.product import ProductDTO
from sqlalchemy import select

async def get_categories() -> list[str]:
    async for session in get_session():
        result = await session.scalars(select(Category.name))
        return result.all()

async def get_products_by_category(category_name: str) -> list[ProductDTO]:
    async for session in get_session():
        stmt = (
            select(Product)
            .join(Category)
            .where(Category.name == category_name)
        )
        result = await session.scalars(stmt)
        products = result.all()
        return [ProductDTO.from_orm(p) for p in products]

async def get_product(product_id: int) -> ProductDTO:
    async for session in get_session():
        product = await session.get(Product, product_id)
        if product:
            return ProductDTO.from_orm(product)
        return None