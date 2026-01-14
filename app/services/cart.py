from sqlalchemy import select, delete
from app.db.session import SessionLocal
from app.db.models import Product, User
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, ForeignKey

Base = declarative_base()

class CartItem(Base):
    __tablename__ = "cart_items"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    grams = Column(Integer, default=0)

async def add_to_cart(user_id: int, product_id: int, delta: int):
    async with SessionLocal() as session:
        item = await session.get(CartItem, (user_id, product_id))
        if not item:
            item = CartItem(user_id=user_id, product_id=product_id, grams=0)
            session.add(item)
        item.grams = max(0, item.grams + delta)
        if item.grams == 0:
            await session.delete(item)
        await session.commit()

async def get_cart(user_id: int):
    async with SessionLocal() as session:
        res = await session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.user_id == user_id)
        )
        return res.all()

async def clear_cart(user_id: int):
    async with SessionLocal() as session:
        await session.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await session.commit()