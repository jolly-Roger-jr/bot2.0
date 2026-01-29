#!/usr/bin/env python3
"""
Добавление полного обработчика для изображений
"""
print("🔧 Завершение добавления обработчика для изображений")
print("=" * 60)

with open("admin.py", "r") as f:
    content = f.read()

# Найдем функцию process_product_category_create (после waiting_product_category)
# Сначала найдем ее определение
import re

# Найдем позицию где начинается process_product_category_create
match = re.search(r'async def process_product_category_create', content)
if match:
    start_pos = match.start()
    print("✅ Найдена функция process_product_category_create")
    
    # Найдем где она заканчивается (поищем следующую async def или конец файла)
    next_func = re.search(r'async def \w+', content[start_pos+1:])
    if next_func:
        end_pos = start_pos + next_func.start()
    else:
        end_pos = len(content)
    
    # Теперь вставим новый обработчик перед этой функцией
    before_func = content[:start_pos]
    after_func = content[start_pos:]
    
    # Создаем новый обработчик для изображений
    image_handler = '''@admin_router.message(AdminStates.waiting_product_image)
async def process_product_image(message: Message, state: FSMContext):
    """Обработка изображения товара"""
    image_url = None
    
    if message.text and message.text.strip().lower() in ['пропустить', 'skip', 'без изображения']:
        await message.answer("✅ Пропускаем загрузку изображения")
    elif message.photo:
        # В реальном боте здесь должна быть загрузка на сервер или в телеграм
        # Для примера используем file_id от телеграма
        image_url = message.photo[-1].file_id
        await message.answer(f"✅ Изображение получено")
    else:
        await message.answer("❌ Пожалуйста, загрузите изображение или отправьте 'пропустить'")
        return
    
    await state.update_data(image_url=image_url)
    
    # Получаем список категорий из состояния
    data = await state.get_data()
    categories = data.get('available_categories', [])
    
    if not categories:
        await message.answer("❌ Список категорий устарел. Начните заново.")
        await state.clear()
        return
    
    categories_text = "\\n".join([f"{cat.id}. {cat.name}" for cat in categories])
    
    await state.set_state(AdminStates.waiting_product_category)
    
    await message.answer(
        f"✅ Изображение обработано\\n\\n"
        f"Доступные категории:\\n{categories_text}\\n\\n"
        "Шаг 7 из 7: Введите ID категории для товара:"
    )

'''

    # Собираем новый контент
    new_content = before_func + image_handler + after_func
    
    with open("admin.py", "w") as f:
        f.write(new_content)
    
    print("✅ Обработчик изображений добавлен перед process_product_category_create")
    
    # Теперь нужно обновить process_product_unit_type чтобы он переходил к waiting_product_image
    # а не waiting_product_category
    new_content = new_content.replace(
        "await state.set_state(AdminStates.waiting_product_category)",
        "await state.set_state(AdminStates.waiting_product_image)"
    )
    
    # Также обновляем сообщение
    new_content = new_content.replace(
        """    await message.answer(
        f\"✅ Единицы измерения приняты: {unit_name}\n\n\"
        f\"Доступные категории:\n{categories_text}\n\n\"
        \"Шаг 6 из 7: Введите ID категории для товара:\"
    )""",
        """    await message.answer(
        f\"✅ Единицы измерения приняты: {unit_name}\n\n\"
        \"Шаг 6 из 7: Загрузите изображение товара (или отправьте 'пропустить' чтобы продолжить без изображения):\"
    )"""
    )
    
    with open("admin.py", "w") as f:
        f.write(new_content)
    
    print("✅ process_product_unit_type обновлен для перехода к загрузке изображения")
    
else:
    print("❌ Функция process_product_category_create не найдена")

# Проверим результат
print("\n🧪 Проверка добавления:")
with open("admin.py", "r") as f:
    content = f.read()
    
if 'async def process_product_image(' in content:
    print("✅ Обработчик process_product_image добавлен")
else:
    print("❌ Обработчик process_product_image не добавлен")

if 'AdminStates.waiting_product_image' in content:
    print("✅ Состояние waiting_product_image используется")
else:
    print("❌ Состояние waiting_product_image не используется")
