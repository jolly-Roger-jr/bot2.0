#!/usr/bin/env python3
"""
Патч для обновления админки с поддержкой единиц измерения
"""
import os

print("🔧 Обновление админки для поддержки единиц измерения")
print("=" * 60)

# Создаем резервную копию
if os.path.exists("admin.py"):
    import shutil
    shutil.copy2("admin.py", "admin.py.backup")
    print("✅ Создана резервная копия admin.py")

# Читаем текущий файл
with open("admin.py", "r") as f:
    content = f.read()

# 1. Обновляем состояния AdminStates
if "class AdminStates(StatesGroup):" in content:
    print("✅ Найдены состояния AdminStates")
    
    # Ищем и обновляем список состояний
    lines = content.split('\n')
    new_lines = []
    
    found_states = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        if "class AdminStates(StatesGroup):" in line:
            found_states = True
        elif found_states and "waiting_product_category = State()" in line:
            # Добавляем новые состояния после waiting_product_category
            new_lines.append("    waiting_product_unit_type = State()")
            new_lines.append("    waiting_product_image = State()")
            new_lines.append("    waiting_edit_field = State()")
            new_lines.append("    waiting_edit_value = State()")
    
    content = '\n'.join(new_lines)
    
    print("✅ Состояния AdminStates обновлены")

# 2. Обновляем функцию process_product_stock_create для запроса единиц измерения
if "async def process_product_stock_create(message: Message, state: FSMContext):" in content:
    print("✅ Найдена функция process_product_stock_create")
    
    # Находим и обновляем эту функцию
    lines = content.split('\n')
    new_lines = []
    in_function = False
    skip_until_state = False
    
    for i, line in enumerate(lines):
        if "async def process_product_stock_create(message: Message, state: FSMContext):" in line:
            in_function = True
            new_lines.append(line)
        elif in_function and line.strip().startswith("await state.set_state(AdminStates.waiting_product_category)"):
            # Вместо этого переходим к выбору единиц измерения
            new_lines.append("        await state.set_state(AdminStates.waiting_product_unit_type)")
            new_lines.append("        ")
            new_lines.append("        await message.answer(")
            new_lines.append("            f\"✅ Количество принято: {stock}\\n\\n\"")
            new_lines.append("            \"Шаг 5 из 7: Выберите единицы измерения товара:\\n\"")
            new_lines.append("            \"1. Граммы (измеряется в граммах, шаг 100г)\\n\"")
            new_lines.append("            \"2. Штуки (измеряется в штуках, шаг 1шт)\\n\\n\"")
            new_lines.append("            \"Введите '1' или '2':\"")
            new_lines.append("        )")
            skip_until_state = True
        elif skip_until_state and line.strip().startswith("@"):
            # Завершили функцию, добавляем новые обработчики
            new_lines.append("")
            new_lines.append("")
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
            new_lines.append("        f\"✅ Единицы измерения приняты: {unit_name}\\n\\n\"")
            new_lines.append("        f\"Доступные категории:\\n{categories_text}\\n\\n\"")
            new_lines.append("        \"Шаг 6 из 7: Введите ID категории для товара:\"")
            new_lines.append("    )")
            new_lines.append("")
            new_lines.append("")
            new_lines.append("@admin_router.message(AdminStates.waiting_product_image)")
            new_lines.append("async def process_product_image(message: Message, state: FSMContext):")
            new_lines.append("    \"\"\"Обработка изображения товара (пока заглушка)\"\"\"")
            new_lines.append("    # TODO: Реализовать загрузку изображений")
            new_lines.append("    image_url = None  # Пока без изображения")
            new_lines.append("    ")
            new_lines.append("    await state.update_data(image_url=image_url)")
            new_lines.append("    ")
            new_lines.append("    # Создаем товар")
            new_lines.append("    data = await state.get_data()")
            new_lines.append("    ")
            new_lines.append("    from database import get_session, Product")
            new_lines.append("    ")
            new_lines.append("    async with get_session() as session:")
            new_lines.append("        product = Product(")
            new_lines.append("            name=data[\"product_name\"],")
            new_lines.append("            description=data.get(\"description\", \"\"),")
            new_lines.append("            price=data[\"price\"],")
            new_lines.append("            stock_grams=data[\"stock\"],")
            new_lines.append("            unit_type=data[\"unit_type\"],")
            new_lines.append("            measurement_step=data[\"measurement_step\"],")
            new_lines.append("            category_id=data.get(\"category_id\"),")
            new_lines.append("            available=True,")
            new_lines.append("            is_active=True,")
            new_lines.append("            image_url=None  # Пока без изображения")
            new_lines.append("        )")
            new_lines.append("        ")
            new_lines.append("        session.add(product)")
            new_lines.append("        await session.commit()")
            new_lines.append("        await session.refresh(product)")
            new_lines.append("    ")
            new_lines.append("    # Получаем название категории")
            new_lines.append("    async with get_session() as session:")
            new_lines.append("        from database import Category")
            new_lines.append("        category = await session.get(Category, data[\"category_id\"])")
            new_lines.append("        category_name = category.name if category else \"Неизвестно\"")
            new_lines.append("    ")
            new_lines.append("    unit_text = \"г\" if data[\"unit_type\"] == \"grams\" else \"шт\"")
            new_lines.append("    ")
            new_lines.append("    await message.answer(")
            new_lines.append("        f\"✅ Товар успешно создан!\\n\\n\"")
            new_lines.append("        f\"📦 Название: {product.name}\\n\"")
            new_lines.append("        f\"📝 Описание: {data.get('description', 'Нет')}\\n\"")
            new_lines.append("        f\"💰 Цена: {product.price} RSD/100{unit_text}\\n\"")
            new_lines.append("        f\"⚖️ Количество: {product.stock_grams}{unit_text}\\n\"")
            new_lines.append("        f\"📏 Единицы: {data['unit_name']}\\n\"")
            new_lines.append("        f\"📂 Категория: {category_name}\\n\\n\"")
            new_lines.append("        f\"🆔 ID: {product.id}\"")
            new_lines.append("    )")
            new_lines.append("    ")
            new_lines.append("    await state.clear()")
            new_lines.append("    ")
            new_lines.append("    # Возвращаем в админ панель")
            new_lines.append("    from keyboards import admin_main_keyboard")
            new_lines.append("    await message.answer(")
            new_lines.append("        \"👑 Админ панель\\n\\nВыберите действие:\",")
            new_lines.append("        reply_markup=admin_main_keyboard()")
            new_lines.append("    )")
            new_lines.append("")
            new_lines.append(line)
            skip_until_state = False
            in_function = False
        elif skip_until_state:
            # Пропускаем старый код
            continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    print("✅ Функция process_product_stock_create обновлена")

# 3. Обновляем process_product_category_create для перехода к шагу с изображением
if "async def process_product_category_create(message: Message, state: FSMContext):" in content:
    print("✅ Найдена функция process_product_category_create")
    
    lines = content.split('\n')
    new_lines = []
    in_function = False
    replaced = False
    
    for i, line in enumerate(lines):
        if "async def process_product_category_create(message: Message, state: FSMContext):" in line:
            in_function = True
            new_lines.append(line)
        elif in_function and "await state.clear()" in line and not replaced:
            # Вместо создания товара здесь, просто сохраняем category_id и переходим к шагу изображения
            # Находим блок создания товара и заменяем его
            pass
        elif in_function and "# Создаем товар" in line and not replaced:
            # Заменяем весь блок создания товара
            new_lines.append("        # Сохраняем ID категории и переходим к следующему шагу")
            new_lines.append("        await state.update_data(category_id=category_id)")
            new_lines.append("        await state.set_state(AdminStates.waiting_product_image)")
            new_lines.append("        ")
            new_lines.append("        await message.answer(")
            new_lines.append("            f\"✅ Категория принята: {category.name}\\n\\n\"")
            new_lines.append("            \"Шаг 7 из 7: Отправьте изображение товара (фото)\\n\"")
            new_lines.append("            \"Или отправьте 'пропустить' чтобы добавить без изображения:\"")
            new_lines.append("        )")
            new_lines.append("        ")
            new_lines.append("        replaced = True")
            # Пропускаем старый код до конца функции
            skip_until_end = True
        elif in_function and skip_until_end and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
            # Конец функции
            new_lines.append("")
            in_function = False
            skip_until_end = False
            new_lines.append(line)
        elif skip_until_end:
            # Пропускаем старый код
            continue
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    print("✅ Функция process_product_category_create обновлена")

# Записываем обновленный файл
with open("admin.py", "w") as f:
    f.write(content)

print("\n🎯 Админка обновлена для поддержки единиц измерения!")
print("\n📋 Добавлены:")
print("   - Выбор единиц измерения (граммы/штуки)")
print("   - Поддержка разных шагов измерения (100г или 1шт)")
print("   - Подготовка для загрузки изображений")
