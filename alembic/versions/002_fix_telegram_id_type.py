"""fix telegram_id type to string

Revision ID: 002_fix_telegram_id_type
Revises: add_full_schema
Create Date: 2026-01-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_fix_telegram_id_type'
down_revision = 'add_full_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Если telegram_id уже имеет тип INTEGER, конвертируем в TEXT
    # Создаем временную таблицу
    op.create_table(
        'users_temp',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('last_active', sa.DateTime(timezone=True)),
    )

    # Копируем данные с конвертацией
    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT * FROM users")).fetchall()

    for user in users:
        # Конвертируем telegram_id в строку
        telegram_id = str(user[1])

        conn.execute(
            sa.text("""
                    INSERT INTO users_temp (id, telegram_id, username, full_name, phone, address, created_at,
                                            last_active)
                    VALUES (:id, :telegram_id, :username, :full_name, :phone, :address, :created_at, :last_active)
                    """),
            {
                'id': user[0],
                'telegram_id': telegram_id,
                'username': user[2],
                'full_name': user[3],
                'phone': user[4],
                'address': user[5],
                'created_at': user[6],
                'last_active': user[7]
            }
        )

    # Удаляем старую таблицу и переименовываем
    op.drop_table('users')
    op.rename_table('users_temp', 'users')

    # Создаем индекс
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)


def downgrade() -> None:
    # Обратная миграция: строку → целое число (если возможно)
    op.create_table(
        'users_old',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('last_active', sa.DateTime(timezone=True)),
    )

    conn = op.get_bind()
    users = conn.execute(sa.text("SELECT * FROM users")).fetchall()

    for user in users:
        try:
            telegram_id = int(user[1]) if user[1] else 0
        except (ValueError, TypeError):
            telegram_id = 0

        conn.execute(
            sa.text("""
                    INSERT INTO users_old (id, telegram_id, username, full_name, phone, address, created_at,
                                           last_active)
                    VALUES (:id, :telegram_id, :username, :full_name, :phone, :address, :created_at, :last_active)
                    """),
            {
                'id': user[0],
                'telegram_id': telegram_id,
                'username': user[2],
                'full_name': user[3],
                'phone': user[4],
                'address': user[5],
                'created_at': user[6],
                'last_active': user[7]
            }
        )

    op.drop_table('users')
    op.rename_table('users_old', 'users')
    op.create_index('ix_users_telegram_id', 'users', ['telegram_id'], unique=True)