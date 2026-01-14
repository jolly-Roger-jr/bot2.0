from aiogram import Router, F
from aiogram.types import Message
from app.config import ADMIN_ID
from app.db.session import SessionLocal
from app.db.models import Product

router = Router()

@router.message(F.text.startswith("/add_product"))
async def add_product(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    # формат:
    # /add_product Название | описание | цена | категория_id
    try:
        _, data = message.text.split(" ", 1)
        name, desc, price, cat_id = [x.strip() for x in data.split("|")]

        async with SessionLocal() as session:
            session.add(Product(
                name=name,
                description=desc,
                price_per_100g=int(price),
                category_id=int(cat_id),
                stock=0,
                stock_type="bulk"
            ))
            await session.commit()

        await message.answer("✅ Товар добавлен")

    except Exception as e:
        await message.answer("❌ Ошибка. Формат:\n/add_product Название | описание | цена | категория_id")