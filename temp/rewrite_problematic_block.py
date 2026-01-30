with open('../handlers.py', 'r') as f:
    lines = f.readlines()

# Найдем начало блока (примерно строка 370)
start_idx = 370
for i in range(370, 400):
    if 'text = (' in lines[i]:
        start_idx = i
        break

# Перепишем блок с правильным форматированием
# Строки 385-392 содержат проблему
# Лучший подход: создать полностью новый блок
new_lines = []
for i in range(len(lines)):
    if i >= 380 and i <= 400:
        # Пропускаем старый проблемный блок, заменим его позже
        continue
    new_lines.append(lines[i])

# Вставляем правильный блок на место старого
# Находим где вставить
for i in range(len(new_lines)):
    if 'text = (' in new_lines[i] and i > 380:
        insert_idx = i
        # Вставляем правильный блок
        correct_block = '''        # Формируем текст

        description = product.get("description", "") or ""

        text = (
            f"🦴 {product['name']}\\n\\n"
            f"{description}\\n\\n"
        )

        # Отображение цены в зависимости от типа товара
        if product.get('unit_type', 'grams') == 'grams':
            price_display = f"💰 Цена: {product['price']} RSD/100г\\n"
        else:
            price_display = f"💰 Цена: {product['price']} RSD/шт\\n"
        
        # Добавляем цену и наличие
        text += price_display
        text += f"📦 В наличии: {product['stock']}{'г' if product.get('unit_type', 'grams') == 'grams' else 'шт'}\\n"
        text += f"🛒 В корзине: {current_in_cart}{'г' if product.get('unit_type', 'grams') == 'grams' else 'шт'}\\n\\n"
        text += "Выберите количество:"'''
        
        # Заменяем старые строки
        new_lines[i] = correct_block + '\n'
        break

with open('../handlers.py', 'w') as f:
    f.writelines(new_lines)
print("Переписан проблемный блок")
