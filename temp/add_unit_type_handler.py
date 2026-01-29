#!/usr/bin/env python3
"""
Добавление обработчика выбора единиц измерения в админку
"""
import os

print("🔧 Добавление обработчика выбора единиц измерения")
print("=" * 60)

with open("admin.py", "r") as f:
    lines = f.readlines()

# Находим функцию process_product_category_create
insert_position = -1
for i, line in enumerate(lines):
    if "async def process_product_category_create(message: Message, state: FSMContext):" in line:
        insert_position = i
        break

if insert_position == -1:
    print("❌ Не найдена функция process_product_category_create")
    exit(1)

# Создаем новый список строк с добавленным обработчиком
new_lines = []
for i, line in enumerate(lines):
    if i == insert_position:
        # Вставляем новый обработчик перед process_product_category_create
        new_lines.append("@admin_router.message(AdminStates.waiting_product_unit_type)")
        new_lines.append("async def process_product_unit_type(message: Message, state: FSMContext):")
        new_lines.append("    \"\"\"Обработка выбора единиц измерения\"\"\"")
        new_lines.append("    unit_choice = message.text.strip()")
        new_lines.append("    ")
        new_lines.append("    if unit_choice == '1':")
        new_lines.append("        unit_type = 'grams'")
        new_lines.append("        measurement_step = 100")
        new_lines.append("        unit_name = 'граммы'")
        new_lines.append("    elif unit_choice == '2':")
        new_lines.append("        unit_type = 'pieces'")
        new_lines.append("        measurement_step = 1")
        new_lines.append("        unit_name = 'штуки'")
        new_lines.append("    else:")
        new_lines.append("        await message.answer(\"❌ Введите '1' или '2'. Введите снова:\")")
        new_lines.append("        return")
        new_lines.append("    ")
        new_lines.append("    await state.update_data(")
        new_lines.append("        unit_type=unit_type,")
        new_lines.append("        measurement_step=measurement_step,")
        new_lines.append("        unit_name=unit_name")
        new_lines.append("    )")
        new_lines.append("    await state.set_state(AdminStates.waiting_product_category)")
        new_lines.append("    ")
        new_lines.append("    # Получаем список категорий из состояния")
        new_lines.append("    data = await state.get_data()")
        new_lines.append("    categories = data.get('available_categories', [])")
        new_lines.append("    ")
        new_lines.append("    if not categories:")
        new_lines.append("        await message.answer(\"❌ Список категорий устарел. Начните заново.\")")
        new_lines.append("        await state.clear()")
        new_lines.append("        return")
        new_lines.append("    ")
        new_lines.append("    categories_text = \"\\n\".join([f\"{cat.id}. {cat.name}\" for cat in categories])")
        new_lines.append("    ")
        new_lines.append("    await message.answer(")
        new_lines.append("        f\"✅ Единицы измерения приняты: {unit_name}\\\\n\\\\n\"")
        new_lines.append("        f\"Доступные категории:\\\\n{categories_text}\\\\n\\\\n\"")
        new_lines.append("        \"Шаг 6 из 7: Введите ID категории для товара:\"")
        new_lines.append("    )")
        new_lines.append("")
        new_lines.append("")
    
    new_lines.append(line)

# Записываем обновленный файл
with open("admin.py", "w") as f:
    f.writelines(new_lines)

print("✅ Обработчик process_product_unit_type добавлен")
print("\n🎯 Админка обновлена!")
