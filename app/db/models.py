from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.engine import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"))
    category = relationship("Category", back_populates="products")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)

    # telegram user id, НЕ FK
    user_id = Column(String, index=True, nullable=False)

    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)


# ⛔ User ВРЕМЕННО УБРАН
# Он тебе сейчас НЕ НУЖЕН
# Добавим позже, когда появятся заказы / профили