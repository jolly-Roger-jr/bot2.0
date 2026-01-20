import asyncio
from app.db.session import get_session
from app.db.models import Category, Product


async def init():
    """Инициализация тестовых данных"""
    async for session in get_session():
        # Проверяем есть ли уже категории
        from sqlalchemy import select
        result = await session.execute(select(Category))
        existing_categories = result.scalars().all()

        if existing_categories:
            print("✅ База данных уже инициализирована")
            return

        # Создаем тестовые категории
        categories = [
            Category(name="Мясные лакомства"),
            Category(name="Печенье для собак"),
            Category(name="Сухие лакомства"),
        ]

        for category in categories:
            session.add(category)

        await session.commit()

        # Создаем тестовые товары
        products = [
            Product(
                name="Говяжьи уши",
                description="Натуральные сушеные говяжьи уши",
                price=250.0,
                category_id=1,
                stock_grams=1500,
                available=True
            ),
            Product(
                name="Говяжья печень",
                description="Сушеная говяжья печень",
                price=300.0,
                category_id=1,
                stock_grams=2000,
                available=True
            ),
            Product(
                name="Морковное печенье",
                description="Печенье с морковью для собак",
                price=180.0,
                category_id=2,
                stock_grams=3500,
                available=True
            ),
            Product(
                name="Тыквенные чипсы",
                description="Сушеные тыквенные чипсы",
                price=220.0,
                category_id=2,
                stock_grams=2800,
                available=True
            ),
        ]

        for product in products:
            session.add(product)

        await session.commit()
        print("✅ База данных инициализирована с тестовыми данными")


# УДАЛИТЕ ЭТО! Не вызывайте asyncio.run() здесь
# asyncio.run(init())

# Вместо этого добавляем функцию для ручного запуска
def init_database():
    """Функция для инициализации БД (вызывается вручную)"""
    return init()