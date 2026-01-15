# app/services/catalog.py
from sqlalchemy import select
from app.db.engine import SessionLocal
from app.db.models import Category, Product


async def get_categories() -> list[str]:
    """
    Вернуть список названий категорий.
    """
    async with SessionLocal() as session:
        result = await session.execute(select(Category.name))
        return [row[0] for row in result.fetchall()]


async def get_products(category_name: str) -> list[dict]:
    """
    Вернуть список товаров заданной категории.
    Каждый товар — словарь с полями id, name, price, description.
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(
                Product.id,
                Product.name,
                Product.price,
                Product.description
            ).join(Category).where(Category.name == category_name)
        )
        rows = result.fetchall()

    # Приводим Decimal -> float, описание может быть None
    return [
        {
            "id": row[0],
            "name": row[1],
            "price": float(row[2]),
            "description": row[3] or ""
        }
        for row in rows
    ]