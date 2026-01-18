from aiogram import Router, F
from aiogram.types import Message
from app.config import settings  # ✅ Импортируем settings
from app.db.session import get_session
from app.db.models import Product

router = Router()

@router.message(F.text.startswith("/add_product"))
async def add_product(message: Message):
    if message.from_user.id != settings.admin_id:  # ✅ Используем settings.admin_id
        return

    # формат:
    # /add_product Название | описание | цена | категория_id
    try:
        _, data = message.text.split(" ", 1)
        name, desc, price, cat_id = [x.strip() for x in data.split("|")]

        async for session in get_session():
            product = Product(
                name=name,
                description=desc,
                price=float(price),
                category_id=int(cat_id)
            )
            session.add(product)
            await session.commit()

        await message.answer("✅ Товар добавлен")

    except Exception as e:
        await message.answer("❌ Ошибка. Формат:\n/add_product Название | описание | цена | категория_id")