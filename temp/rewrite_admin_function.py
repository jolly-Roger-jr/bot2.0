#!/usr/bin/env python3
"""
Переписываем функцию process_product_unit_type правильно
"""
import os

print("🔧 Переписываем функцию process_product_unit_type")
print("=" * 60)

with open("admin.py", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if i == 370:  # Строка 371 (0-based индекс 370)
        # Это начало функции, заменяем ее правильной версией
        new_lines.append("@admin_router.message(AdminStates.waiting_product_unit_type)\n")
        new_lines.append("async def process_product_unit_type(message: Message, state: FSMContext):\n")
        new_lines.append("    \"\"\"Обработка выбора единиц измерения\"\"\"\n")
        new_lines.append("    unit_choice = message.text.strip()\n")
        new_lines.append("    \n")
        new_lines.append("    if unit_choice == '1':\n")
        new_lines.append("        unit_type = 'grams'\n")
        new_lines.append("        measurement_step = 100\n")
        new_lines.append("        unit_name = 'граммы'\n")
        new_lines.append("    elif unit_choice == '2':\n")
        new_lines.append("        unit_type = 'pieces'\n")
        new_lines.append("        measurement_step = 1\n")
        new_lines.append("        unit_name = 'штуки'\n")
        new_lines.append("    else:\n")
        new_lines.append("        await message.answer(\"❌ Введите '1' или '2'. Введите снова:\")\n")
        new_lines.append("        return\n")
        new_lines.append("    \n")
        new_lines.append("    await state.update_data(\n")
        new_lines.append("        unit_type=unit_type,\n")
        new_lines.append("        measurement_step=measurement_step,\n")
        new_lines.append("        unit_name=unit_name\n")
        new_lines.append("    )\n")
        new_lines.append("    await state.set_state(AdminStates.waiting_product_category)\n")
        new_lines.append("    \n")
        new_lines.append("    # Получаем список категорий из состояния\n")
        new_lines.append("    data = await state.get_data()\n")
        new_lines.append("    categories = data.get('available_categories', [])\n")
        new_lines.append("    \n")
        new_lines.append("    if not categories:\n")
        new_lines.append("        await message.answer(\"❌ Список категорий устарел. Начните заново.\")\n")
        new_lines.append("        await state.clear()\n")
        new_lines.append("        return\n")
        new_lines.append("    \n")
        new_lines.append("    categories_text = \"\\n\".join([f\"{cat.id}. {cat.name}\" for cat in categories])\n")
        new_lines.append("    \n")
        new_lines.append("    await message.answer(\n")
        new_lines.append("        f\"✅ Единицы измерения приняты: {unit_name}\\\\n\\\\n\"\n")
        new_lines.append("        f\"Доступные категории:\\\\n{categories_text}\\\\n\\\\n\"\n")
        new_lines.append("        \"Шаг 6 из 7: Введите ID категории для товара:\"\n")
        new_lines.append("    )\n")
    elif i == 371:  # Следующая строка - это начало process_product_category_create
        # Проверим что это за строка
        if "async def process_product_category_create" in line:
            # Это отдельная функция, оставляем ее
            new_lines.append(line)
        else:
            # Это часть предыдущей функции, пропускаем
            continue
    else:
        new_lines.append(line)

# Записываем исправленный файл
with open("admin.py", "w") as f:
    f.writelines(new_lines)

print("✅ Функция process_product_unit_type переписана правильно")

# Проверим
print("\n🧪 Проверяем строки 365-380:")
with open("admin.py", "r") as f:
    lines = f.readlines()
    for i in range(364, 380):
        if i < len(lines):
            line_num = i + 1
            print(f"{line_num:3}: {lines[i].rstrip()}")
