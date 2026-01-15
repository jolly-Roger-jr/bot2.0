import os
from sqlalchemy import create_engine, inspect

# Путь к базе
DB_PATH = "./app/db/barkery.db"

if not os.path.exists(DB_PATH):
    print(f"❌ Файл базы {DB_PATH} не найден!")
else:
    print(f"✅ Файл базы {DB_PATH} найден.")

# Создаем движок
engine = create_engine(f"sqlite:///{DB_PATH}")

# Создаем инспектор для проверки таблиц
inspector = inspect(engine)
tables = inspector.get_table_names()

if tables:
    print(f"✅ Таблицы в базе: {tables}")
else:
    print("⚠️ Таблиц в базе не найдено!")