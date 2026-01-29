#!/usr/bin/env python3
"""
Патч для обновления хендлеров с поддержкой единиц измерения
"""
import os

print("🔧 Обновление хендлеров для поддержки единиц измерения")
print("=" * 60)

# Создаем резервную копию
if os.path.exists("handlers.py"):
    import shutil
    shutil.copy2("handlers.py", "handlers.py.backup")
    print("✅ Создана резервная копия handlers.py")

# Читаем текущий файл
with open("handlers.py", "r") as f:
    content = f.read()

# 1. Обновляем функцию show_product для правильного отображения единиц
lines = content.split('\n')
new_lines = []
in_show_product = False
skip_until_end = False

for i, line in enumerate(lines):
    if "async def show_product(callback: CallbackQuery):" in line:
        in_show_product = True
        new_lines.append(line)
    elif in_show_product and "# Получаем количество в корзине" in line:
        # Добавляем определение единиц измерения
        new_lines.append("        # Определяем единицы измерения")
        new_lines.append("        unit_type = product.get('unit_type', 'grams')")
        new_lines.append("        measurement_step = product.get('measurement_step', 100)")
        new_lines.append("        unit_symbol = 'г' if unit_type == 'grams' else 'шт'")
        new_lines.append("        step_text = '100г' if unit_type == 'grams' else '1шт'")
        new_lines.append("        ")
        new_lines.append(line)
    elif in_show_product and "# Формируем текст" in line:
        # Обновляем формирование текста
        new_lines.append("        # Формируем текст")
        new_lines.append("        description = product.get(\"description\", \"\") or \"\"")
        new_lines.append("        price_per_unit = product['price']")
        new_lines.append("        ")
        new_lines.append("        if unit_type == 'grams':")
        new_lines.append("            price_text = f\"{price_per_unit} RSD/100г\"")
        new_lines.append("        else:")
        new_lines.append("            price_text = f\"{price_per_unit} RSD/шт\"")
        new_lines.append("        ")
        new_lines.append("        text = (")
        new_lines.append("            f\"🦴 {product['name']}\\n\\n\"")
        new_lines.append("            f\"{description}\\n\\n\"")
        new_lines.append("            f\"💰 Цена: {price_text}\\n\"")
        new_lines.append("            f\"📦 В наличии: {product['stock_grams']}{unit_symbol}\\n\"")
        new_lines.append("            f\"🛒 В корзине: {current_in_cart}{unit_symbol}\\n\\n\"")
        new_lines.append("            \"Выберите количество:\"")
        new_lines.append("        )")
        new_lines.append("        ")
        skip_until_end = True
    elif in_show_product and skip_until_end and "keyboard = product_card_keyboard(product_id, category_id, temp_qty)" in line:
        new_lines.append("        ")
        new_lines.append("        keyboard = product_card_keyboard(")
        new_lines.append("            product_id=product_id,")
        new_lines.append("            category_id=category_id,")
        new_lines.append("            current_qty=temp_qty,")
        new_lines.append("            unit_type=unit_type,")
        new_lines.append("            measurement_step=measurement_step")
        new_lines.append("        )")
        skip_until_end = False
    elif skip_until_end:
        # Пропускаем старый код
        continue
    elif in_show_product and line.strip() and not line.startswith(" ") and not line.startswith("\t") and line != "":
        # Конец функции
        in_show_product = False
        new_lines.append(line)
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# 2. Обновляем функцию handle_quantity
lines = content.split('\n')
new_lines = []
in_handle_quantity = False
skip_until_end = False

for i, line in enumerate(lines):
    if "async def handle_quantity(callback: CallbackQuery):" in line:
        in_handle_quantity = True
        new_lines.append(line)
    elif in_handle_quantity and "# Определяем дельту" in line:
        new_lines.append("        # Определяем дельту на основе единиц измерения")
        new_lines.append("        # Нужно получить информацию о товаре для определения шага")
        new_lines.append("        product = await catalog_service.get_product(product_id)")
        new_lines.append("        if not product:")
        new_lines.append("            await callback.answer(\"❌ Товар не найден\", show_alert=True)")
        new_lines.append("            return")
        new_lines.append("        ")
        new_lines.append("        unit_type = product.get('unit_type', 'grams')")
        new_lines.append("        measurement_step = product.get('measurement_step', 100)")
        new_lines.append("        ")
        new_lines.append("        # Определяем дельту")
        new_lines.append("        delta = -measurement_step if action == \"qty_dec\" else measurement_step")
        new_lines.append(line)
    elif in_handle_quantity and "# Получаем текущее количество в корзине" in line:
        # Добавляем информацию о единицах
        new_lines.append("        # Определяем символ единиц")
        new_lines.append("        unit_symbol = 'г' if unit_type == 'grams' else 'шт'")
        new_lines.append("        ")
        new_lines.append(line)
    elif in_handle_quantity and "await callback.answer(f\"Предварительное количество: {new_temp}г\")" in line:
        # Обновляем текст ответа
        new_lines.append(f"            await callback.answer(f\"Предварительное количество: {new_temp}{unit_symbol}\")")
        skip_until_end = True
    elif skip_until_end:
        # Пропускаем старый код
        continue
    elif in_handle_quantity and line.strip() and not line.startswith(" ") and not line.startswith("\t") and line != "":
        # Конец функции
        in_handle_quantity = False
        new_lines.append(line)
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# 3. Обновляем функцию add_to_cart
lines = content.split('\n')
new_lines = []
in_add_to_cart = False
skip_until_end = False

for i, line in enumerate(lines):
    if "async def add_to_cart(callback: CallbackQuery):" in line:
        in_add_to_cart = True
        new_lines.append(line)
    elif in_add_to_cart and "await callback.answer(f\"✅ Добавлено в корзину: {quantity}г\")" in line:
        # Получаем информацию о товаре для единиц
        new_lines.append("            # Получаем информацию о товаре для единиц")
        new_lines.append("            product = await catalog_service.get_product(product_id)")
        new_lines.append("            unit_symbol = 'г' if product.get('unit_type', 'grams') == 'grams' else 'шт'")
        new_lines.append("            ")
        new_lines.append(f"            await callback.answer(f\"✅ Добавлено в корзину: {quantity}{unit_symbol}\")")
        skip_until_end = True
    elif skip_until_end:
        # Пропускаем старый код
        continue
    elif in_add_to_cart and line.strip() and not line.startswith(" ") and not line.startswith("\t") and line != "":
        # Конец функции
        in_add_to_cart = False
        new_lines.append(line)
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Записываем обновленный файл
with open("handlers.py", "w") as f:
    f.write(content)

print("✅ Хендлеры обновлены для поддержки единиц измерения")
print("\n🎯 Обновления применены!")
print("\n📋 Изменения в handlers.py:")
print("   - show_product: теперь учитывает unit_type")
print("   - handle_quantity: дельта зависит от measurement_step")
print("   - add_to_cart: показывает правильные единицы")
