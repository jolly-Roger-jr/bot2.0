#!/usr/bin/env python3
"""
Добавление функции admin_product_edit_keyboard в keyboards.py
"""
import os

print("🔧 Добавление admin_product_edit_keyboard")
print("=" * 60)

with open("keyboards.py", "r") as f:
    content = f.read()

# Найдем конец файла и добавим функцию
lines = content.split('\n')
new_lines = []

# Ищем конец файла или последнюю функцию
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Если это последняя строка, добавляем функцию перед ней
    if i == len(lines) - 1:
        # Добавляем новую функцию
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
    f.write('\n'.join(new_lines))

print("✅ Функция admin_product_edit_keyboard добавлена")

# Проверим
print("\n🧪 Проверяем добавление:")
try:
    from keyboards import admin_product_edit_keyboard
    print("✅ Функция импортируется")
    
    # Тестируем создание
    kb = admin_product_edit_keyboard(1, 1)
    print(f"✅ Клавиатура создана: {len(kb.inline_keyboard)} ряда")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Keyboards.py обновлен!")
