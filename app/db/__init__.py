"""
Database package for Barkery_bot
"""

from .engine import engine, SessionLocal, Base
from .session import get_session
from .models import User, Category, Product, CartItem, Order, OrderItem
from .backup import DatabaseBackup, backup_manager, backup_database

__all__ = [
    'engine',
    'SessionLocal',
    'Base',
    'get_session',
    'User',
    'Category',
    'Product',
    'CartItem',
    'Order',
    'OrderItem',
    'DatabaseBackup',    # ← Добавлено
    'backup_manager',    # ← Теперь существует
    'backup_database'    # ← Теперь существует
]