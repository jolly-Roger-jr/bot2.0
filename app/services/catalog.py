from sqlalchemy import select
from app.db.models import Category, Product
from app.db.engine import SessionLocal

async def get_categories():
    async with SessionLocal() as session:
        result = await session.execute(select(Category.name))
        return [row[0] for row in result.fetchall()]

async def get_products(category_name: str):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Product.name).join(Category).where(Category.name == category_name)
        )
        return [row[0] for row in result.fetchall()]