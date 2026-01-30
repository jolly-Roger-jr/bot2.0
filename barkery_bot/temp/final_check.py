#!/usr/bin/env python3
"""
Финальная проверка синтаксиса и логики
Создан: 2026-01-30 15:00
"""

import ast
import sys

def check_python_syntax(file_path):
    """Проверяет синтаксис Python файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем синтаксис
        ast.parse(content)
        print(f"✅ {file_path}: Синтаксис корректен")
        return True
        
    except SyntaxError as e:
        print(f"❌ {file_path}: Синтаксическая ошибка")
        print(f"   Строка {e.lineno}: {e.msg}")
        print(f"   Текст: {e.text}")
        return False
    except Exception as e:
        print(f"❌ {file_path}: Ошибка при проверке: {e}")
        return False

def check_imports(file_path):
    """Проверяет наличие необходимых импортов"""
    required_imports = [
        'InlineKeyboardMarkup',
        'InlineKeyboardButton'
    ]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing = []
        for imp in required_imports:
            if imp not in content:
                missing.append(imp)
        
        if missing:
            print(f"⚠️  {file_path}: Отсутствуют импорты: {missing}")
            return False
        else:
            print(f"✅ {file_path}: Все импорты на месте")
            return True
            
    except Exception as e:
        print(f"❌ {file_path}: Ошибка при проверке импортов: {e}")
        return False

# Проверяем основные файлы
files_to_check = ['handlers.py', 'admin.py', 'services.py', 'keyboards.py']

print("=== ПРОВЕРКА СИНТАКСИСА ===")
all_ok = True
for file in files_to_check:
    if not check_python_syntax(file):
        all_ok = False

print("\n=== ПРОВЕРКА ИМПОРТОВ ===")
check_imports('handlers.py')

if all_ok:
    print("\n✅ Все файлы имеют корректный синтаксис")
else:
    print("\n❌ Обнаружены ошибки синтаксиса")
    sys.exit(1)

# Дополнительная проверка
print("\n=== ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ ===")
print("1. Проверка функции show_product...")
with open('handlers.py', 'r', encoding='utf-8') as f:
    content = f.read()
    if 'send_photo' in content:
        print("   ✅ Функция send_photo используется")
    else:
        print("   ❌ Функция send_photo не найдена")
    
    if '24 часов' not in content:
        print("   ✅ Текст о доставке удален")
    else:
        print("   ❌ Текст о доставке не удален")

print("\n2. Проверка бэкапов...")
import os
backup_files = os.listdir('barkery_bot/backup')
if len(backup_files) > 0:
    print(f"   ✅ Создано {len(backup_files)} бэкапов")
    # Проверяем количество бэкапов handlers.py
    handlers_backups = [f for f in backup_files if 'handlers' in f]
    if len(handlers_backups) > 2:
        print(f"   ⚠️  Слишком много бэкапов handlers.py ({len(handlers_backups)})")
        print("   Рекомендуется удалить старые бэкапы")
    else:
        print(f"   ✅ Количество бэкапов handlers.py: {len(handlers_backups)}")
else:
    print("   ⚠️  Бэкапы не созданы")
