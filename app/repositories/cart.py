from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CartItem  # ✅ Меняем импорт


async def get_cart(session: AsyncSession, user_id: int):
    result = await session.scalars(
        select(CartItem).where(CartItem.user_id == user_id)
    )
    return result.all()