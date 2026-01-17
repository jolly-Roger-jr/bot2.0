# app/services/cart.py

from sqlalchemy import select, delete
from app.db.session import get_session
from app.db.models import CartItem, Product


async def add_to_cart(user_id: int, product_id: int, quantity: int):
    async for session in get_session():
        result = await session.execute(
            select(CartItem).where(
                CartItem.user_id == str(user_id),
                CartItem.product_id == product_id
            )
        )
        item = result.scalar_one_or_none()

        if item:
            item.quantity += quantity
        else:
            product = await session.get(Product, product_id)
            if not product:
                return

            item = CartItem(
                user_id=str(user_id),
                product_id=product_id,
                quantity=quantity,
                price=product.price
            )
            session.add(item)

        await session.commit()


async def get_cart_items(user_id: int):
    async for session in get_session():
        result = await session.execute(
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.user_id == str(user_id))
        )

        items = []
        for cart_item, product in result.all():
            cart_item.product = product  # 👈 чтобы handler мог читать item.product.name
            items.append(cart_item)

        return items


async def clear_cart(user_id: int):
    async for session in get_session():
        await session.execute(
            delete(CartItem).where(CartItem.user_id == str(user_id))
        )
        await session.commit()