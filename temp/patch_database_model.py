#!/usr/bin/env python3
"""
Патч для обновления модели Product в database.py
"""
import os

print("🔧 Обновление модели Product")
print("=" * 60)

# Создаем резервную копию
if os.path.exists("database.py"):
    import shutil
    shutil.copy2("database.py", "database.py.backup")
    print("✅ Создана резервная копия database.py")

# Читаем текущий файл
with open("database.py", "r") as f:
    content = f.read()

# Ищем модель Product
if "class Product(Base):" in content:
    print("✅ Найдена модель Product")
    
    # Проверяем наличие нужных полей
    if "unit_type" not in content:
        print("❌ Поле unit_type отсутствует - добавляем")
        
        # Находим позицию для вставки после stock_grams
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if "stock_grams = Column(Integer, default=0, nullable=False)" in line:
                # Добавляем новые поля после stock_grams
                new_lines.append("    unit_type = Column(String, default='grams', nullable=False)  # 'grams' или 'pieces'")
                new_lines.append("    measurement_step = Column(Integer, default=100, nullable=False)  # шаг измерения (100 для грамм, 1 для штук)")
                new_lines.append("    is_active = Column(Boolean, default=True, nullable=False)  # активен ли товар")
        
        content = '\n'.join(new_lines)
        
        # Записываем обновленный файл
        with open("database.py", "w") as f:
            f.write(content)
        
        print("✅ Модель Product обновлена")
    else:
        print("✅ Поле unit_type уже присутствует")
else:
    print("❌ Не найдена модель Product")

# Проверяем обновления
print("\n🧪 Проверяем обновления:")
with open("database.py", "r") as f:
    lines = f.readlines()
    in_product_class = False
    for i, line in enumerate(lines):
        if "class Product(Base):" in line:
            in_product_class = True
        elif in_product_class and line.startswith("class "):
            in_product_class = False
        
        if in_product_class and ("unit_type" in line or "measurement_step" in line or "is_active" in line):
            print(f"   ✅ {line.strip()}")

print("\n🎯 Модель базы данных обновлена!")
