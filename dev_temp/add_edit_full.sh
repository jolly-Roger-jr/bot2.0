#!/bin/bash
# Добавляем простой обработчик для admin_edit_product_full

# Находим где вставить (перед admin_edit_product_description)
line_num=$(grep -n "@admin_router.callback_query(F.data.startswith(\"admin_edit_product_description:\")" admin.py)
if [ -z "$line_num" ]; then
    line_num=$(grep -n "# ========== ПРОВЕРКА ВСЕХ ТОВАРОВ ==========" admin.py)
fi

line_num=$(echo "$line_num" | head -1 | cut -d: -f1)

if [ -n "$line_num" ]; then
    # Создаем временный файл
    head -n $((line_num - 1)) admin.py > admin_new.py
    
    # Добавляем новый обработчик
    cat >> admin_new.py << 'PYEOF'

# ========== РЕДАКТИРОВАНИЕ ТОВАРА (МЕНЮ) ==========

@admin_router.callback_query(F.data.startswith("admin_edit_product_full:"))
async def admin_edit_product_full_handler(callback: CallbackQuery):
    """Меню редактирования товара (полная карточка)"""
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    parts = callback.data.split(":")
    product_id = int(parts[1])
    category_id = int(parts[2])

    async with get_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        # Показываем меню редактирования
        unit_text = "гр" if product.unit_type == 'grams' else "шт"
        stock_text = f"{product.stock_grams}{unit_text}"
        status = "✅ Доступен" if product.available else "⛔ Скрыт"
        
        await callback.message.edit_text(
            f"✏️ Редактирование товара\n\n"
            f"📦 Название: {product.name}\n"
            f"📝 Описание: {product.description or 'Нет описания'}\n"
            f"💰 Цена: {product.price} RSD/{'100г' if product.unit_type == 'grams' else 'шт'}\n"
            f"📦 Остатки: {stock_text}\n"
            f"📏 Единицы: {product.unit_type} (шаг: {product.measurement_step})\n"
            f"🖼️ Изображение: {'Есть' if product.image_url else 'Нет'}\n"
            f"📊 Статус: {status}\n\n"
            f"Выберите что редактировать:"
        )

    await callback.answer()

PYEOF
    
    # Добавляем остаток файла
    tail -n +$line_num admin.py >> admin_new.py
    
    # Заменяем файл
    mv admin.py admin_backup2.py
    mv admin_new.py admin.py
    echo "Добавлен обработчик admin_edit_product_full"
fi
