from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cart_item import CartItem

async def get_cart(session: AsyncSession, user_id: int):
    result = await session.scalars(
        select(CartItem).where(CartItem.user_id == user_id)
    )
    return result.all()