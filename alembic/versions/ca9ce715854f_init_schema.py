"""init schema

Revision ID: ca9ce715854f
Revises: 
Create Date: 2026-01-15 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ca9ce715854f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Создание всех таблиц."""
    # Пользователи
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('telegram_id', sa.Integer, nullable=False, unique=True),
        sa.Column('username', sa.String, nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('instagram', sa.String, nullable=True),
        sa.Column('phone', sa.String, nullable=True),
        sa.Column('pet_name', sa.String, nullable=True),
        sa.Column('pet_breed', sa.String, nullable=True),
        sa.Column('note', sa.Text, nullable=True),
    )

    # Категории
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False, unique=True),
    )

    # Товары
    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('category_id', sa.Integer, sa.ForeignKey('categories.id'), nullable=False),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.UniqueConstraint('category_id', 'name', name='uq_product_category_name'),
    )

    # Корзина
    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('products.id'), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.UniqueConstraint('user_id', 'product_id', name='uq_cart_user_product'),
    )


def downgrade() -> None:
    """Удаление всех таблиц (откат)."""
    op.drop_table('cart_items')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')
