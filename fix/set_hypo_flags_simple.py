# set_hypo_flags_simple.py
# !/usr/bin/env python3
"""
Простой скрипт для установки флагов гипоаллергенности
Работает напрямую с SQLite, без SQLAlchemy
"""
import sqlite3
import os


def update_hypo_flags():
    """Обновить флаги гипоаллергенности"""
    db_path = "../barkery.db"

    if not os.path.exists(db_path):
        print(f"❌ Файл БД не найден: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Проверяем наличие поля
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'is_hypoallergenic' not in column_names:
            print("❌ Поле 'is_hypoallergenic' не найдено!")
            return

        # 2. Получаем все товары
        print("🔍 Загружаю товары...")
        cursor.execute("SELECT id, name, description FROM products")
        products = cursor.fetchall()

        print(f"📊 Найдено {len(products)} товаров")

        # 3. Ключевые слова для гипоаллергенных товаров
        hypo_keywords = [
            'гипо', 'аллерген', 'аллергия', 'гипоаллерген',
            'без аллерген', 'низкоаллерген', 'hypo', 'allerg',
            'for sensitive', 'чувствительн', 'для аллергиков',
            'sensitive', 'allergy', 'беззерновой', 'без зерна',
            'без глютена', 'глютен'
        ]

        updated = 0

        # 4. Обновляем каждый товар
        for product_id, name, description in products:
            name_lower = (name or "").lower()
            desc_lower = (description or "").lower()

            # Проверяем ключевые слова
            is_hypo = False
            for keyword in hypo_keywords:
                if keyword in name_lower or keyword in desc_lower:
                    is_hypo = True
                    break

            # Обновляем если нужно
            cursor.execute(
                "UPDATE products SET is_hypoallergenic = ? WHERE id = ?",
                (1 if is_hypo else 0, product_id)
            )

            if is_hypo:
                updated += 1
                short_name = name[:30] + "..." if len(name) > 30 else name
                print(f"✓ {short_name}")

        conn.commit()

        # 5. Статистика
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_hypoallergenic = 1")
        hypo_count = cursor.fetchone()[0]

        print(f"\n📊 Статистика:")
        print(f"• Всего товаров: {len(products)}")
        print(f"• Помечено как гипоаллергенные: {hypo_count}")
        print(f"• Обновлено в этом запуске: {updated}")

        print("\n✅ Готово!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔄 Установка флагов гипоаллергенности...")
    print("=" * 50)
    update_hypo_flags()
    print("=" * 50)