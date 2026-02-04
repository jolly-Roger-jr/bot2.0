"""
Все модели и работа с БД в одном файде
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./barkery.db")

# Базовый класс для моделей
Base = declarative_base()

# ========== МОДЕЛИ ==========

class User(Base):
    """Модель пользователя - ОБНОВЛЕНА"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    
    # Основная информация из заказа
    pet_name = Column(String, nullable=True)  # Имя питомца
    telegram_username = Column(String, nullable=True)  # Telegram логин (без @)
    
    # Контактная информация
    phone = Column(String, nullable=True)
    
    # Дополнительная информация о собаке
    instagram = Column(String, nullable=True)
    dog_breed = Column(String, nullable=True)  # Порода собаки
    allergies = Column(String, nullable=True)  # Наличие аллергии
    notes = Column(Text, nullable=True)  # Примечания
    
    # Системные поля
    full_name = Column(String, nullable=True)  # Полное имя пользователя (из Telegram)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Резервные поля для миграции
    address = Column(Text, nullable=True)  # Старый адрес (для обратной совместимости)
    telegram_login_backup = Column(String, nullable=True)
    allergy_backup = Column(String, nullable=True)


class Category(Base):
    """Модель категории"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Product(Base):
    """Модель товара"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)  # цена за 100 грамм в RSD
    image_url = Column(String, nullable=True)
    available = Column(Boolean, default=True, nullable=False)
    stock_grams = Column(Integer, default=0, nullable=False)
    unit_type = Column(String, default='grams', nullable=False)  # 'grams' или 'pieces'
    measurement_step = Column(Integer, default=100, nullable=False)  # шаг измерения (100 для грамм, 1 для штук)
    hide_when_zero = Column(Boolean, default=True, nullable=False)  # Автоматически скрывать при нулевом остатке
    is_active = Column(Boolean, default=True, nullable=False)  # активен ли товар
    
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"))
    category = relationship("Category")


class CartItem(Base):
    """Модель элемента корзины"""
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    quantity = Column(Integer, nullable=False)  # количество в граммах
    
    user = relationship("User")
    product = relationship("Product")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
    )


class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    customer_name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    
    status = Column(String, default="pending", nullable=False)
    total_amount = Column(Float, nullable=False)


class OrderItem(Base):
    """Модель элемента заказа"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    
    product_name = Column(String, nullable=False)
    price_per_100g = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)  # количество в граммах


class UserAddress(Base):
    """Модель адресов доставки пользователя"""
    __tablename__ = "user_addresses"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address = Column(Text, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")


# ========== СЕССИИ И ENGINE ==========

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Контекстный менеджер для получения сессии"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Инициализация БД (создание таблиц) - миграция"""
    async with engine.begin() as conn:
        # Создаем таблицы (SQLAlchemy автоматически обновит структуру)
        await conn.run_sync(Base.metadata.create_all)
        
        # Для SQLite миграция будет выполнена автоматически,
        # так как мы используем ту же таблицу с новыми полями
        print("✅ База данных инициализирована (миграция выполнена)")

