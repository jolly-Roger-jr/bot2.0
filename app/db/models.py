from sqlalchemy import (
    Column, Integer, String, Boolean,
    ForeignKey, Text, DateTime, Enum, BigInteger
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

class StockType(enum.Enum):
    bulk = "bulk"
    unit = "unit"


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    price_per_100g = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)
    stock_type = Column(Enum(StockType))
    unit_to_grams = Column(Integer, default=100)
    image = Column(String)
    is_active = Column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True)
    username = Column(String)
    phone = Column(String)
    pet_name = Column(String)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_price = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_name = Column(String)
    grams = Column(Integer)
    price = Column(Integer)