#!/usr/bin/env python3
"""
Анализ структуры проекта Barkery Bot
"""
import os
import re

print("=== АНАЛИЗ ПРОЕКТА BARKERY BOT ===")
print()

# 1. Проверка импортов и зависимостей
print("1. ОСНОВНЫЕ ИМПОРТЫ В handlers.py:")
with open("handlers.py", "r") as f:
    content = f.read()
    
    # Находим все импорты
    imports = re.findall(r'^import .*|^from .* import .*', content, re.MULTILINE)
    for imp in imports[:15]:
        print(f"   {imp}")

print()

# 2. Проверка обработчиков для работы с изображениями
print("2. ОБРАБОТЧИКИ ДЛЯ ИЗОБРАЖЕНИЙ:")
if "photo" in content or "image_url" in content:
    print("   ✅ Есть обработка изображений")
else:
    print("   ❌ Нет обработки изображений")

# 3. Проверка навигации
print("\n3. НАВИГАЦИЯ И КНОПКА 'НАЗАД':")
back_handlers = re.findall(r'def.*back.*\(|CallbackQuery.*back', content)
for handler in back_handlers[:10]:
    print(f"   {handler}")

# 4. Проверка структуры обработчиков товаров
print("\n4. СТРУКТУРА ОБРАБОТЧИКОВ ТОВАРОВ:")
product_handlers = re.findall(r'def show_product.*\(|@router.*product:', content)
for handler in product_handlers[:10]:
    print(f"   {handler}")

# 5. Проверка наличия обработки фото сообщений
print("\n5. ПРОВЕРКА ОБРАБОТКИ СООБЩЕНИЙ С ФОТО:")
if "callback.message.photo" in content or "callback.message.edit_caption" in content:
    print("   ✅ Есть обработка сообщений с фото")
else:
    print("   ❌ Нет обработки сообщений с фото")

print("\n=== АНАЛИЗ ЗАВЕРШЕН ===")
