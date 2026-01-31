#!/usr/bin/env python3
"""
Добавляем недостающие колонки в таблицу users
"""
import sqlite3
import sys

def add_missing_columns():
    """Добавляем недостающие колонки"""
    try:
        conn = sqlite3.connect('barkery.db')
        cursor = conn.cursor()
        
        print("=== ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ ПОЛЕЙ ===")
        
        # Проверяем текущую структуру
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Текущие поля: {columns}")
        
        # Поля которые нужно добавить
        columns_to_add = [
            ('notes', 'TEXT'),
            ('instagram', 'TEXT'),
            ('dog_breed', 'TEXT'),
            ('allergies', 'TEXT'),
            ('last_order_date', 'TIMESTAMP')
        ]
        
        added_count = 0
        for column_name, column_type in columns_to_add:
            if column_name not in columns:
                print(f"Добавляем поле: {column_name} ({column_type})")
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    added_count += 1
                except sqlite3.OperationalError as e:
                    print(f"  Ошибка при добавлении {column_name}: {e}")
            else:
                print(f"Поле {column_name} уже существует")
        
        conn.commit()
        
        if added_count > 0:
            print(f"\n✅ Добавлено {added_count} полей")
        else:
            print("\n✅ Все поля уже существуют")
        
        # Проверяем итоговую структуру
        cursor.execute("PRAGMA table_info(users)")
        print("\n=== ИТОГОВАЯ СТРУКТУРА ===")
        for col in cursor.fetchall():
            print(f"{col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_missing_columns()
    sys.exit(0 if success else 1)
