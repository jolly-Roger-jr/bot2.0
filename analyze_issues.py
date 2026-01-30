import sys
import os

print("=== АНАЛИЗ ПРОБЛЕМ BARKERY_BOT ===")
print("\n1. ПРОБЛЕМЫ С ШТУЧНЫМИ ТОВАРАМИ:")
print("   - В models.py поле stock_grams используется для всех товаров")
print("   - В services.py цена всегда делится на 100 (строка 145)")
print("   - В handlers.py всегда отображается 'г' (строки 679, 818, 954)")
print("   - В cart_service.add_to_cart проверка stock_grams для всех товаров")
print("   - В БД товар ID6 имеет unit_type='pieces' но stock_grams=10")

print("\n2. ПРОБЛЕМЫ С АДМИНКОЙ:")
print("   - Редактор товаров не сохраняет unit_type после добавления изображения")
print("   - Нет отдельного поля stock_pieces для штучных товаров")

print("\n3. ПРОБЛЕМЫ С НАВИГАЦИЕЙ:")
print("   - Иногда появляется qwerty-клавиатура вместо inline-кнопок")
print("   - Возможно, проблема в обработчиках или состоянии бота")

print("\n4. СТРУКТУРНЫЕ ПРОБЛЕМЫ:")
print("   - Необходимо разделение stock_grams на stock_amount")
print("   - Нужна логика расчета цены в зависимости от unit_type")
print("   - Нужно правильное отображение единиц измерения")

print("\nРЕКОМЕНДУЕМЫЕ ИСПРАВЛЕНИЯ:")
print("1. Изменить модель Product:")
print("   - Добавить stock_amount вместо stock_grams")
print("   - Или использовать stock_grams для грамм, stock_pieces для штук")
print("2. Исправить services.py:")
print("   - Расчет цены в зависимости от unit_type")
print("   - Проверка наличия с учетом unit_type")
print("3. Исправить handlers.py:")
print("   - Отображение правильных единиц измерения")
print("   - Исправление текстовых сообщений")
print("4. Исправить keyboards.py:")
print("   - Уже корректно работает с unit_type")
print("5. Исправить admin.py:")
print("   - Сохранение unit_type при редактировании")
