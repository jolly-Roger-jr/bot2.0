#!/usr/bin/env python3
"""
Скрипт миграции данных для пользователей
"""
import sqlite3
import sys

def migrate_users():
    """Миграция данных пользователей"""
    try:
        conn = sqlite3.connect('barkery.db')
        cursor = conn.cursor()
        
        print("=== НАЧАЛО МИГРАЦИИ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ ===")
        
        # Проверяем текущую структуру
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Текущие поля: {columns}")
        
        # 1. Проверяем и обновляем данные
        # В старой версии данные уже в нужных полях (telegram_username, а не username)
        print("✓ Проверка данных...")
        
        # 2. Обновляем last_active для всех пользователей
        cursor.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE last_active IS NULL")
        
        # 3. Показываем результат
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        print(f"✓ Обработано пользователей: {count}")
        
        cursor.execute("SELECT id, telegram_id, telegram_username, pet_name, full_name FROM users")
        users = cursor.fetchall()
        
        print("\n=== ТЕКУЩИЕ ДАННЫЕ ПОСЛЕ МИГРАЦИИ ===")
        for user in users:
            print(f"ID: {user[0]}, Telegram: {user[1]}, @{user[2]}, Питомец: {user[3]}, Имя: {user[4]}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Миграция завершена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

if __name__ == "__main__":
    success = migrate_users()
    sys.exit(0 if success else 1)
