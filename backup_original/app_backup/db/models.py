# app/db/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.engine import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)  # цена за 100 грамм в RSD
    image_url = Column(String, nullable=True)  # URL изображения товара
    available = Column(Boolean, default=True, nullable=False)  # доступен ли товар
    stock_grams = Column(Integer, default=0, nullable=False)  # остатки в граммах ← ВАЖНОЕ ПОЛЕ

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    category = relationship("Category", back_populates="products")

    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True, nullable=False)  # Telegram ID как строка

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, nullable=False)  # количество в граммах

    product = relationship("Product", back_populates="cart_items")

    # Убрано поле price - цена всегда берется из Product


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)  # Telegram ID покупателя
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Контактные данные
    customer_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=False)

    # Статус заказа
    status = Column(String, default="pending", nullable=False)  # pending, confirmed, completed, cancelled

    # Стоимость
    total_amount = Column(Float, nullable=False)  # общая сумма в RSD

    # Связи
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id"))

    product_name = Column(String, nullable=False)  # название товара на момент заказа
    price_per_100g = Column(Float, nullable=False)  # цена за 100г на момент заказа
    quantity = Column(Integer, nullable=False)  # количество в граммах

    # Связи
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")