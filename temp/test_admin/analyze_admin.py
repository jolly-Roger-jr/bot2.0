#!/usr/bin/env python3
"""
Анализ структуры админки
"""
import sys
import os
import inspect
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from admin import admin_router, AdminStates
from aiogram import F
from aiogram.filters import Command

# Проверяем зарегистрированные хендлеры
print("📋 Зарегистрированные хендлеры в admin_router:")
for handler in admin_router.message.handlers:
    if hasattr(handler, 'filters'):
        print(f"  📝 Message handler: {handler}")
        for f in handler.filters:
            print(f"    Filter: {f}")

print("\n📋 Callback хендлеры:")
for handler in admin_router.callback_query.handlers:
    if hasattr(handler, 'filters'):
        print(f"  📝 Callback handler: {handler.callback.__name__ if hasattr(handler.callback, '__name__') else handler.callback}")
        for f in handler.filters:
            if hasattr(f, 'callback'):
                print(f"    Filter: {f.callback.__name__ if hasattr(f.callback, '__name__') else f.callback}")
            else:
                print(f"    Filter: {f}")

# Проверяем состояния
print("\n📋 Состояния AdminStates:")
states = [state for state in dir(AdminStates) if not state.startswith('_')]
for state in states:
    print(f"  • {state}")

# Проверяем обработчик пошагового редактирования
print("\n🔍 Поиск обработчика admin_edit_product_full:")
import admin as admin_module
for name in dir(admin_module):
    obj = getattr(admin_module, name)
    if callable(obj) and 'edit_product' in name.lower():
        print(f"  ⚙️ Функция: {name}")
