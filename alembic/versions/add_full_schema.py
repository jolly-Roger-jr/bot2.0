# alembic/versions/add_full_schema.py
"""add_full_schema

Revision ID: add_full_schema
Revises:
Create Date: 2026-01-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_full_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создание всех таблиц по новой схеме."""
    # Категории
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True),
    )

    # Товары (с полными полями по ТЗ)
    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Float, nullable=False),  # цена за 100г в RSD
        sa.Column('image_url', sa.String, nullable=True),
        sa.Column('available', sa.Boolean, default=True, nullable=False),
        sa.Column('stock_grams', sa.Integer, default=0, nullable=False),
        sa.UniqueConstraint('category_id', 'name', name='uq_product_category_name'),
    )

    # Корзина
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.String, nullable=False, index=True),  # Telegram ID как строка
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),  # количество в граммах
        sa.UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
    )

    # Заказы
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.String, nullable=False),  # Telegram ID покупателя
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('customer_name', sa.String, nullable=True),
        sa.Column('phone', sa.String, nullable=True),
        sa.Column('address', sa.Text, nullable=False),
        sa.Column('status', sa.String, default='pending', nullable=False),
        sa.Column('total_amount', sa.Float, nullable=False),
    )

    # Элементы заказа
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.id'), nullable=True),
        sa.Column('product_name', sa.String, nullable=False),
        sa.Column('price_per_100g', sa.Float, nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
    )


def downgrade() -> None:
    """Удаление всех таблиц (откат)."""
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('products')
    op.drop_table('categories')