from app.db.session import get_session
from app.db.models import Category, Product
import asyncio

async def init():
    async for session in get_session():
        cat1 = Category(name="Сухие лакомства")
        cat2 = Category(name="Консервы")
        session.add_all([cat1, cat2])
        await session.commit()

        prod1 = Product(name="Лакомство 1", price=150, category_id=cat1.id)
        prod2 = Product(name="Лакомство 2", price=200, category_id=cat1.id)
        session.add_all([prod1, prod2])
        await session.commit()

asyncio.run(init())