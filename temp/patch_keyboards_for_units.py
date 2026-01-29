#!/usr/bin/env python3
"""
Патч для обновления клавиатур с поддержкой единиц измерения
"""
import os

print("🔧 Обновление клавиатур для поддержки единиц измерения")
print("=" * 60)

# Создаем резервную копию
if os.path.exists("keyboards.py"):
    import shutil
    shutil.copy2("keyboards.py", "keyboards.py.backup")
    print("✅ Создана резервная копия keyboards.py")

# Читаем текущий файл
with open("keyboards.py", "r") as f:
    content = f.read()

# 1. Обновляем функцию product_card_keyboard
if "def product_card_keyboard(product_id: int, category_id: int, current_qty: int = 0) -> InlineKeyboardMarkup:" in content:
    print("✅ Найдена функция product_card_keyboard")
    
    # Заменяем сигнатуру функции
    content = content.replace(
        "def product_card_keyboard(product_id: int, category_id: int, current_qty: int = 0) -> InlineKeyboardMarkup:",
        "def product_card_keyboard(product_id: int, category_id: int, current_qty: int = 0, unit_type: str = 'grams', measurement_step: int = 100) -> InlineKeyboardMarkup:"
    )
    
    # Ищем и заменяем логику внутри функции
    lines = content.split('\n')
    new_lines = []
    in_function = False
    replaced_qty_logic = False
    
    for i, line in enumerate(lines):
        if "def product_card_keyboard(" in line and "-> InlineKeyboardMarkup:" in line:
            in_function = True
            new_lines.append(line)
        elif in_function and "# Количество в единицах по 100г" in line:
            # Заменяем логику расчета количества
            new_lines.append("    # Количество в единицах измерения")
            new_lines.append("    if unit_type == 'grams':")
            new_lines.append("        qty_units = current_qty // measurement_step")
            new_lines.append("        unit_text = f'{measurement_step}г'")
            new_lines.append("        unit_symbol = 'г'")
            new_lines.append("    else:  # pieces")
            new_lines.append("        qty_units = current_qty")
            new_lines.append("        unit_text = 'шт'")
            new_lines.append("        unit_symbol = 'шт'")
            new_lines.append("    ")
            replaced_qty_logic = True
        elif in_function and "qty_100g = current_qty // 100" in line:
            # Пропускаем старую строку
            continue
        elif in_function and "qty_100g" in line and replaced_qty_logic:
            # Заменяем использование qty_100g на qty_units
            new_line = line.replace("qty_100g", "qty_units")
            new_lines.append(new_line)
        elif in_function and "f\"{qty_100g} × 100г\"" in line:
            # Заменяем текст кнопки
            new_lines.append(f"            text=f\"{{qty_units}} × {unit_text}\",")
        elif in_function and "add_qty = qty_100g * 100" in line:
            # Заменяем логику расчета добавляемого количества
            new_lines.append("    if unit_type == 'grams':")
            new_lines.append("        add_qty = qty_units * measurement_step")
            new_lines.append("    else:  # pieces")
            new_lines.append("        add_qty = qty_units")
        elif in_function and "if add_qty > 0:" in line:
            # Оставляем как есть, но обновим текст кнопки ниже
            new_lines.append(line)
        elif in_function and "f\"🛒 Добавить ({add_qty}г)\"" in line:
            # Обновляем текст кнопки с правильными единицами
            new_lines.append(f"                text=f'🛒 Добавить ({{add_qty}}{{unit_symbol}})',")
        elif in_function and line.strip() and not line.startswith(" ") and not line.startswith("\t") and line != "":
            # Конец функции
            in_function = False
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    print("✅ Функция product_card_keyboard обновлена")

# 2. Добавляем функцию для управления товарами в админке с учетом единиц
lines = content.split('\n')
new_lines = []

# Находим конец файла и добавляем новую функцию перед ним
for i, line in enumerate(lines):
    new_lines.append(line)
    if line.strip() == "# ========== АДМИНСКИЕ КЛАВИАТУРЫ ==========":
        # Добавляем новую функцию после этого заголовка
        new_lines.append("")
        new_lines.append("def admin_product_edit_keyboard(product_id: int, category_id: int) -> InlineKeyboardMarkup:")
        new_lines.append("    \"\"\"Клавиатура редактирования товара\"\"\"")
        new_lines.append("    builder = InlineKeyboardBuilder()")
        new_lines.append("    ")
        new_lines.append("    builder.row(")
        new_lines.append("        InlineKeyboardButton(")
        new_lines.append("            text=\"✏️ Изменить название\",")
        new_lines.append("            callback_data=f\"admin_edit_product_name:{product_id}:{category_id}\"")
        new_lines.append("        )")
        new_lines.append("    )")
        new_lines.append("    ")
        new_lines.append("    builder.row(")
        new_lines.append("        InlineKeyboardButton(")
        new_lines.append("            text=\"💰 Изменить цену\",")
        new_lines.append("            callback_data=f\"admin_edit_product_price:{product_id}:{category_id}\"")
        new_lines.append("        )")
        new_lines.append("    )")
        new_lines.append("    ")
        new_lines.append("    builder.row(")
        new_lines.append("        InlineKeyboardButton(")
        new_lines.append("            text=\"📦 Изменить остатки\",")
        new_lines.append("            callback_data=f\"admin_edit_product_stock:{product_id}:{category_id}\"")
        new_lines.append("        )")
        new_lines.append("    )")
        new_lines.append("    ")
        new_lines.append("    builder.row(")
        new_lines.append("        InlineKeyboardButton(")
        new_lines.append("            text=\"📏 Изменить единицы\",")
        new_lines.append("            callback_data=f\"admin_edit_product_units:{product_id}:{category_id}\"")
        new_lines.append("        )")
        new_lines.append("    )")
        new_lines.append("    ")
        new_lines.append("    builder.row(")
        new_lines.append("        InlineKeyboardButton(")
        new_lines.append("            text=\"⬅️ Назад\",")
        new_lines.append("            callback_data=f\"admin_category_products:{category_id}\"")
        new_lines.append("        ),")
        new_lines.append("        InlineKeyboardButton(")
        new_lines.append("            text=\"🏠 В главное\",")
        new_lines.append("            callback_data=\"admin_back\"")
        new_lines.append("        )")
        new_lines.append("    )")
        new_lines.append("    ")
        new_lines.append("    return builder.as_markup()")
        new_lines.append("")

# Записываем обновленный файл
with open("keyboards.py", "w") as f:
    f.write(content)

print("✅ Клавиатуры обновлены для поддержки единиц измерения")
print("\n🎯 Обновления применены!")
print("\n📋 Изменения в keyboards.py:")
print("   - product_card_keyboard: теперь принимает unit_type и measurement_step")
print("   - Добавлена admin_product_edit_keyboard для редактирования товаров")
