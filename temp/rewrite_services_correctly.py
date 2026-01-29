#!/usr/bin/env python3
"""
Создаем полностью исправленный services.py
"""
import os

print("🔧 Создаем полностью исправленный services.py")
print("=" * 60)

# Прочитаем файл до проблемной строки
with open("services.py", "r") as f:
    content = f.read()

# Найдем проблему - вероятно в функции get_products_by_category
lines = content.split('\n')
new_lines = []

# Идем по строкам и исправляем
i = 0
while i < len(lines):
    line = lines[i]
    
    # Проверяем строку 236 (индекс 235)
    if i == 235:
        print(f"Проверяем строку {i+1}: {line[:50]}...")
        
    # Ищем функцию get_products_by_category
    if "async def get_products_by_category(self, category_id: int) -> List[Dict]:" in line:
        print(f"Найдена функция get_products_by_category на строке {i+1}")
        
        # Копируем сигнатуру
        new_lines.append(line)
        i += 1
        
        # Копируем тело до return
        while i < len(lines) and "return [" not in lines[i]:
            new_lines.append(lines[i])
            i += 1
        
        # Теперь обрабатываем return
        if i < len(lines) and "return [" in lines[i]:
            # Создаем правильный return
            new_lines.append("            return [")
            new_lines.append("                {")
            new_lines.append('                    "id": p.id,')
            new_lines.append('                    "name": p.name,')
            new_lines.append('                    "description": p.description,')
            new_lines.append('                    "price": p.price,')
            new_lines.append('                    "stock_grams": p.stock_grams,')
            new_lines.append('                    "image_url": p.image_url,')
            new_lines.append('                    "available": p.available,')
            new_lines.append('                    "is_active": p.is_active,')
            new_lines.append('                    "unit_type": p.unit_type,')
            new_lines.append('                    "measurement_step": p.measurement_step')
            new_lines.append("                }")
            new_lines.append("                for p in products")
            new_lines.append("            ]")
            
            # Пропускаем старый блок return
            i += 1
            while i < len(lines) and "]" not in lines[i]:
                i += 1
            if i < len(lines):
                i += 1  # Пропускаем закрывающую скобку
        else:
            # Не нашли return, продолжаем как обычно
            new_lines.append(lines[i])
            i += 1
    else:
        new_lines.append(line)
        i += 1

# Теперь убедимся что функция update_product в правильном месте
# Найдем класс CatalogService
final_content = '\n'.join(new_lines)

# Проверим наличие update_product
if "async def update_product" not in final_content:
    print("\n⚠️  Функция update_product отсутствует, добавляем...")
    
    # Найдем где вставить - в конце класса CatalogService
    lines = final_content.split('\n')
    new_final_lines = []
    
    for i, line in enumerate(lines):
        new_final_lines.append(line)
        
        # Ищем строку перед классом UserService или перед созданием экземпляров
        if "class UserService:" in line or "# Создаем экземпляры сервисов" in line:
            # Вставляем update_product перед этим
            insert_index = len(new_final_lines) - 1
            
            new_final_lines.insert(insert_index, "")
            new_final_lines.insert(insert_index + 1, "    async def update_product(self, product_id: int, **kwargs) -> Dict:")
            new_final_lines.insert(insert_index + 2, "        \"\"\"Обновить товар\"\"\"")
            new_final_lines.insert(insert_index + 3, "        async with get_session() as session:")
            new_final_lines.insert(insert_index + 4, "            product = await session.get(Product, product_id)")
            new_final_lines.insert(insert_index + 5, "            if not product:")
            new_final_lines.insert(insert_index + 6, "                return {\"success\": False, \"error\": \"Товар не найден\"}")
            new_final_lines.insert(insert_index + 7, "            ")
            new_final_lines.insert(insert_index + 8, "            # Обновляем только переданные поля")
            new_final_lines.insert(insert_index + 9, "            for key, value in kwargs.items():")
            new_final_lines.insert(insert_index + 10, "                if hasattr(product, key):")
            new_final_lines.insert(insert_index + 11, "                    setattr(product, key, value)")
            new_final_lines.insert(insert_index + 12, "            ")
            new_final_lines.insert(insert_index + 13, "            await session.commit()")
            new_final_lines.insert(insert_index + 14, "            return {\"success\": True, \"product\": product}")
            new_final_lines.insert(insert_index + 15, "")
    
    final_content = '\n'.join(new_final_lines)

# Записываем исправленный файл
with open("services.py", "w") as f:
    f.write(final_content)

print("✅ services.py полностью исправлен")

# Проверим
print("\n🧪 Проверяем исправления:")
try:
    # Попробуем импортировать
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
    
    from services import catalog_service
    print("✅ services.py импортируется")
    
    # Проверим методы
    methods = [m for m in dir(catalog_service) if not m.startswith('_')]
    print(f"✅ Методы catalog_service: {', '.join(methods)}")
    
    if 'update_product' in methods:
        print("✅ update_product присутствует")
    else:
        print("❌ update_product отсутствует")
        
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
