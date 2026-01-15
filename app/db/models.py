from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    instagram = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    pet_name = Column(String, nullable=True)
    pet_breed = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    cart_items = relationship("CartItem", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    __table_args__ = (UniqueConstraint("category_id", "name", name="uq_product_category_name"),)

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)