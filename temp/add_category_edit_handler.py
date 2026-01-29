#!/usr/bin/env python3
"""
Добавление обработчика редактирования категорий
"""
print("🔧 Добавление редактирования категорий")
print("=" * 60)

with open("admin.py", "r") as f:
    content = f.read()

# Добавим новый обработчик перед обработчиком удаления категорий
new_content = content.replace(
    '# Удаление категории',
    '''# Редактирование категории
@admin_router.callback_query(F.data.startswith("admin_edit_category:"))
async def admin_edit_category_handler(callback: CallbackQuery, state: FSMContext):
    """Редактирование категории"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    
    category_id = int(callback.data.split(":")[1])
    
    await state.update_data(edit_category_id=category_id)
    await state.set_state(AdminStates.waiting_edit_category_name)
    
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if category:
            await callback.message.edit_text(
                f"✏️ Редактирование категории\n\n"
                f"Текущее название: {category.name}\n\n"
                "Введите новое название категории:"
            )
    
    await callback.answer()

@admin_router.message(AdminStates.waiting_edit_category_name)
async def process_edit_category_name(message: Message, state: FSMContext):
    """Обработка нового названия категории"""
    new_name = message.text.strip()
    
    if len(new_name) < 2:
        await message.answer("❌ Название слишком короткое. Введите снова:")
        return
    
    data = await state.get_data()
    category_id = data.get("edit_category_id")
    
    async with get_session() as session:
        category = await session.get(Category, category_id)
        if not category:
            await message.answer("❌ Категория не найдена")
            await state.clear()
            return
        
        # Проверяем нет ли другой категории с таким названием
        from sqlalchemy import select
        stmt = select(Category).where(Category.name == new_name, Category.id != category_id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            await message.answer("❌ Категория с таким названием уже существует. Введите другое:")
            return
        
        old_name = category.name
        category.name = new_name
        await session.commit()
        
        await message.answer(f"✅ Категория переименована: {old_name} → {new_name}")
        
        # Возвращаем к списку категорий
        stmt = select(Category).order_by(Category.name)
        result = await session.execute(stmt)
        categories = result.scalars().all()
        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]
        
        from keyboards import admin_categories_keyboard
        await message.answer(
            f"📦 Категории\n\nВсего категорий: {len(categories_list)}",
            reply_markup=admin_categories_keyboard(categories_list)
        )
    
    await state.clear()

# Удаление категории'''
)

with open("admin.py", "w") as f:
    f.write(new_content)

print("✅ Обработчик редактирования категорий добавлен")

# Проверим
print("\n🧪 Проверка добавления:")
with open("admin.py", "r") as f:
    content = f.read()
    
if 'async def admin_edit_category_handler' in content:
    print("✅ Обработчик редактирования категорий добавлен")
else:
    print("❌ Обработчик не добавлен")
