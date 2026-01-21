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
    """Создание всех таблиц (только если их нет)"""
    # Проверяем существование таблиц перед созданием

    # Пользователи
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.String(), unique=True, nullable=False, index=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active', sa.DateTime(timezone=True), server_default=sa.func.now()),
        if_not_exists=True  # Важно: создавать только если не существует
    )

    # Категории
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), unique=True, nullable=False),
        if_not_exists=True
    )

    # Товары
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('available', sa.Boolean(), default=True, nullable=False),
        sa.Column('stock_grams', sa.Integer(), default=0, nullable=False),
        sa.UniqueConstraint('category_id', 'name', name='uq_product_category_name'),
        if_not_exists=True
    )

    # Корзина
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE')),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
        if_not_exists=True
    )

    # Заказы
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('customer_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('address', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), default='pending', nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        if_not_exists=True
    )

    # Элементы заказа
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id')),
        sa.Column('product_name', sa.String(), nullable=False),
        sa.Column('price_per_100g', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        if_not_exists=True
    )


def downgrade() -> None:
    """Удаление всех таблиц (откат)"""
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('cart_items')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')