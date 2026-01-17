# fill_initial_data.py
import asyncio
from sqlalchemy import text, insert, select
from app.db.engine import SessionLocal
from app.db.models import Category, Product

# Начальные данные
CATEGORIES = ["Печенье", "Торты", "Пирожные"]

PRODUCTS = {
    "Печенье": ["Овсяное", "Шоколадное", "Имбирное"],
    "Торты": ["Медовый", "Шоколадный", "Наполеон"],
    "Пирожные": ["Эклер", "Картошка", "Птичье молоко"]
}

async def fill_initial_data():
    async for session in get_session():
        async with session.begin():
            # --- Категории ---
            for cat_name in CATEGORIES:
                result = await session.execute(
                    select(Category).where(Category.name == cat_name)
                )
                existing = result.scalar_one_or_none()
                if not existing:
                    session.add(Category(name=cat_name))

            # --- Продукты ---
            for cat_name, products in PRODUCTS.items():
                result = await session.execute(
                    select(Category).where(Category.name == cat_name)
                )
                category = result.scalar_one()
                for prod_name in products:
                    result = await session.execute(
                        select(Product).where(Product.name == prod_name, Product.category_id == category.id)
                    )
                    existing_prod = result.scalar_one_or_none()
                    if not existing_prod:
                        session.add(
                            Product(
                                name=prod_name,
                                price=100.0,  # можешь поменять цену
                                category_id=category.id
                            )
                        )

        await session.commit()
        print("✅ Начальные данные успешно добавлены!")

if __name__ == "__main__":
    asyncio.run(fill_initial_data())