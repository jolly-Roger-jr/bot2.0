# add_field_manually.py
import sqlite3
import os


def add_field():
    """Добавить поле is_hypoallergenic вручную"""
    db_path = "../barkery.db"

    if not os.path.exists(db_path):
        print(f"❌ Файл БД не найден: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🔍 Проверяю текущую структуру...")
        cursor.execute("PRAGMA table_info(products)")
        columns_before = cursor.fetchall()

        print("До добавления:")
        for col in columns_before:
            print(f"  • {col[1]}")

        # Добавляем поле
        print("\n➕ Добавляю поле 'is_hypoallergenic'...")
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN is_hypoallergenic BOOLEAN 
            DEFAULT 0 
            NOT NULL
        """)

        conn.commit()

        # Проверяем результат
        cursor.execute("PRAGMA table_info(products)")
        columns_after = cursor.fetchall()

        print("\nПосле добавления:")
        for col in columns_after:
            print(f"  • {col[1]}")

        print("\n✅ Поле успешно добавлено!")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✅ Поле уже существует!")
        else:
            print(f"❌ Ошибка SQLite: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    add_field()