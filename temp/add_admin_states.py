#!/usr/bin/env python3
"""
Добавление недостающих состояний в AdminStates
"""
import os

print("🔧 Добавление состояний в AdminStates")
print("=" * 60)

with open("admin.py", "r") as f:
    lines = f.readlines()

new_lines = []
states_added = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Находим класс AdminStates
    if "class AdminStates(StatesGroup):" in line:
        # Следующие строки должны быть состояниями
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith("waiting_"):
            j += 1
        
        # Вставляем новые состояния после существующих
        if j < len(lines):
            new_lines.insert(j, "    waiting_product_unit_type = State()")
            new_lines.insert(j+1, "    waiting_product_image = State()")
            new_lines.insert(j+2, "    waiting_edit_field = State()")
            new_lines.insert(j+3, "    waiting_edit_value = State()")
            states_added = True

# Записываем обновленный файл
with open("admin.py", "w") as f:
    f.writelines(new_lines)

if states_added:
    print("✅ Состояния добавлены в AdminStates")
else:
    print("⚠️  Не удалось найти AdminStates для добавления")

# Проверим
print("\n🧪 Проверяем состояния:")
with open("admin.py", "r") as f:
    lines = f.readlines()
    in_states = False
    for line in lines:
        if "class AdminStates(StatesGroup):" in line:
            in_states = True
        elif in_states and line.strip() and not line.startswith("    "):
            in_states = False
        
        if in_states and "waiting_" in line:
            print(f"   {line.strip()}")

print("\n🎯 Состояния обновлены!")
