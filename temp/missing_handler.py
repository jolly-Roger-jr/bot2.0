@admin_router.message(AdminStates.waiting_product_unit_type)
async def process_product_unit_type_create(message: Message, state: FSMContext):
    """Обработка единиц измерения товара при создании"""
    unit_choice = message.text.strip()
    
    if unit_choice == '1':
        unit_type = 'grams'
        measurement_step = 100
        unit_text = 'грамм'
    elif unit_choice == '2':
        unit_type = 'pieces'
        measurement_step = 1
        unit_text = 'штук'
    else:
        await message.answer("❌ Введите '1' или '2':")
        return
    
    await state.update_data(unit_type=unit_type, measurement_step=measurement_step)
    await state.set_state(AdminStates.waiting_product_image)
    
    await message.answer(
        f"✅ Единицы измерения приняты: {unit_text} (шаг: {measurement_step})\n\n"
        "Шаг 6 из 7: Загрузите изображение товара.\n"
        "Или отправьте 'пропустить' если без изображения:"
    )
