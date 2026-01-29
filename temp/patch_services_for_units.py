#!/usr/bin/env python3
"""
Патч для обновления сервисов с поддержкой единиц измерения
"""
import os

print("🔧 Обновление сервисов для поддержки единиц измерения")
print("=" * 60)

# Создаем резервную копию
if os.path.exists("services.py"):
    import shutil
    shutil.copy2("services.py", "services.py.backup")
    print("✅ Создана резервная копия services.py")

# Читаем текущий файл
with open("services.py", "r") as f:
    content = f.read()

# Обновляем функцию get_product в CatalogService
if "async def get_product(self, product_id: int) -> Optional[Dict]:" in content:
    print("✅ Найдена функция get_product")
    
    lines = content.split('\n')
    new_lines = []
    in_function = False
    
    for i, line in enumerate(lines):
        if "async def get_product(self, product_id: int) -> Optional[Dict]:" in line:
            in_function = True
            new_lines.append(line)
        elif in_function and "if product:" in line:
            new_lines.append(line)
        elif in_function and "return {" in line and in_function:
            # Находим начало возвращаемого словаря
            dict_start = i
            # Ищем конец словаря
            j = i
            while j < len(lines) and ("}" not in lines[j] or lines[j].count('{') != lines[j].count('}')):
                j += 1
            
            # Заменяем весь блок возврата
            new_lines.append("            return {")
            new_lines.append("                \"id\": product.id,")
            new_lines.append("                \"name\": product.name,")
            new_lines.append("                \"description\": product.description,")
            new_lines.append("                \"price\": product.price,")
            new_lines.append("                \"stock_grams\": product.stock_grams,")
            new_lines.append("                \"image_url\": product.image_url,")
            new_lines.append("                \"available\": product.available,")
            new_lines.append("                \"is_active\": product.is_active,")
            new_lines.append("                \"unit_type\": product.unit_type,")
            new_lines.append("                \"measurement_step\": product.measurement_step,")
            new_lines.append("                \"category_id\": product.category_id")
            new_lines.append("            }")
            
            # Пропускаем старый блок
            for k in range(i, j+1):
                if k != i:
                    continue
            in_function = False
        elif in_function:
            # Пропускаем старый код
            continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    print("✅ Функция get_product обновлена")

# Обновляем функцию get_products_by_category
lines = content.split('\n')
new_lines = []
in_function = False
in_return_block = False

for i, line in enumerate(lines):
    if "async def get_products_by_category(self, category_id: int) -> List[Dict]:" in line:
        in_function = True
        new_lines.append(line)
    elif in_function and "return [" in line:
        # Начинается блок возврата
        in_return_block = True
        # Заменяем весь блок
        new_lines.append("            return [")
        new_lines.append("                {")
        new_lines.append("                    \"id\": p.id,")
        new_lines.append("                    \"name\": p.name,")
        new_lines.append("                    \"description\": p.description,")
        new_lines.append("                    \"price\": p.price,")
        new_lines.append("                    \"stock_grams\": p.stock_grams,")
        new_lines.append("                    \"image_url\": p.image_url,")
        new_lines.append("                    \"available\": p.available,")
        new_lines.append("                    \"is_active\": p.is_active,")
        new_lines.append("                    \"unit_type\": p.unit_type,")
        new_lines.append("                    \"measurement_step\": p.measurement_step")
        new_lines.append("                }")
        new_lines.append("                for p in products")
        new_lines.append("            ]")
        in_return_block = False
        in_function = False
    elif in_return_block:
        # Пропускаем старый код
        continue
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Добавляем новую функцию для обновления товара
lines = content.split('\n')
new_lines = []

# Ищем место для добавления новой функции (после get_product)
for i, line in enumerate(lines):
    new_lines.append(line)
    if "async def get_product(self, product_id: int) -> Optional[Dict]:" in line:
        # Находим конец этой функции
        j = i + 1
        while j < len(lines) and not (lines[j].strip().startswith("async def") or lines[j].strip().startswith("def ")):
            j += 1
        
        # Добавляем новую функцию после get_product
        new_lines.append("")
        new_lines.append("    async def update_product(self, product_id: int, **kwargs) -> Dict:")
        new_lines.append("        \"\"\"Обновить товар\"\"\"")
        new_lines.append("        async with get_session() as session:")
        new_lines.append("            product = await session.get(Product, product_id)")
        new_lines.append("            if not product:")
        new_lines.append("                return {\"success\": False, \"error\": \"Товар не найден\"}")
        new_lines.append("            ")
        new_lines.append("            # Обновляем только переданные поля")
        new_lines.append("            for key, value in kwargs.items():")
        new_lines.append("                if hasattr(product, key):")
        new_lines.append("                    setattr(product, key, value)")
        new_lines.append("            ")
        new_lines.append("            await session.commit()")
        new_lines.append("            return {\"success\": True, \"product\": product}")
        new_lines.append("")

# Записываем обновленный файл
with open("services.py", "w") as f:
    f.write(content)

print("✅ Сервисы обновлены для поддержки единиц измерения")
print("\n🎯 Обновления применены!")
print("\n📋 Изменения в services.py:")
print("   - get_product: возвращает unit_type и measurement_step")
print("   - get_products_by_category: возвращает unit_type и measurement_step")
print("   - Добавлена update_product для редактирования товаров")
