# app/repositories/catalog.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Category, Product  # ✅ Исправленный импорт


async def get_categories(session: AsyncSession) -> list[str]:
    result = await session.scalars(select(Category.name))
    return result.all()

async def get_products_by_category(
    session: AsyncSession,
    category_name: str,
) -> list[Product]:
    stmt = (
        select(Product)
        .join(Category)
        .where(Category.name == category_name)
    )
    result = await session.scalars(stmt)
    return result.all()