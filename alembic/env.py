from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.db.base import Base  # твои модели

# Alembic Config object
config = context.config

# Настройка логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаинформация моделей для автогенерации
target_metadata = Base.metadata

# Принудительно полный путь к файлу БД SQLite
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "app/db/barkery.db")
if not os.path.exists(os.path.dirname(db_path)):
    os.makedirs(os.path.dirname(db_path))  # создаём папку, если нет
if not os.path.exists(db_path):
    open(db_path, "a").close()
config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")  # создаём файл, если нет

# Обновляем URL в конфиге
config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()