#!/bin/bash
echo "Применяем исправление в handlers.py..."

# Находим строку с вызовом is_product_available
line_num=$(grep -n "availability = await cart_service.is_product_available(product_id, consider_carts=True)" ./handlers.py | cut -d: -f1)

if [ -n "$line_num" ]; then
    echo "Найдена строка $line_num"
    
    # Создаем временный файл
    head -n $((line_num-1)) ./handlers.py > ./handlers_temp.py
    
    # Добавляем исправленную строку
    cat >> ./handlers_temp.py << 'FIX'
                # Проверяем доступность каждого товара
                availability = await cart_service.is_product_available(
                    product_id, 
                    consider_carts=True, 
                    exclude_user_id=user_id  # ИСКЛЮЧАЕМ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ!
                )
FIX
    
    # Добавляем остаток файла после строки line_num+1
    tail -n +$((line_num+1)) ./handlers.py >> ./handlers_temp.py
    
    # Заменяем файл
    mv ./handlers_temp.py ./handlers.py
    echo "✅ Исправление применено!"
else
    echo "❌ Не найдена строка для замены"
    exit 1
fi
