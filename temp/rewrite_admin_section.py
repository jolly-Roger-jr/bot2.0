#!/usr/bin/env python3
"""
Переписывание проблемного участка в admin.py
"""
print("🔧 Переписывание проблемного участка в admin.py")
print("=" * 60)

with open("admin.py", "r") as f:
    lines = f.readlines()

# Найдем функцию admin_edit_category_handler
start_idx = -1
for i, line in enumerate(lines):
    if 'async def admin_edit_category_handler' in line:
        start_idx = i
        break

if start_idx == -1:
    print("❌ Функция не найдена")
    exit(1)

# Покажем проблемный участок
print("Проблемный участок (строки 150-165):")
for i in range(start_idx, start_idx + 20):
    if i < len(lines):
        print(f"{i+1:3}: {repr(lines[i].rstrip()[:60])}")

# Создаем новую версию этого участка
new_lines = []
i = 0
in_problem_section = False
replaced = False

while i < len(lines):
    # Находим проблемный edit_text вызов
    if 'await callback.message.edit_text(' in lines[i] and not replaced:
        print(f"\n✅ Найден проблемный edit_text на строке {i+1}")
        
        # Копируем строку с edit_text
        new_lines.append(lines[i])
        i += 1
        
        # Следующие строки должны содержать текст сообщения
        # Соберем все строки до закрывающей скобки
        message_lines = []
        bracket_count = 1  # Уже открыли скобку
        j = i
        
        while j < len(lines) and bracket_count > 0:
            line = lines[j]
            message_lines.append(line)
            bracket_count += line.count('(') - line.count(')')
            j += 1
        
        print(f"Найдено {len(message_lines)} строк сообщения")
        
        # Создаем исправленную версию
        new_lines.append('                f"✏️ Редактирование категории\\n\\n"\n')
        new_lines.append('                f"Текущее название: {category.name}\\n\\n"\n')
        new_lines.append('                "Введите новое название категории:"\n')
        
        # Пропускаем старые строки
        i = j
        replaced = True
        continue
    
    new_lines.append(lines[i])
    i += 1

# Записываем обратно
with open("admin.py", "w") as f:
    f.writelines(new_lines)

print("\n✅ Участок переписан")

# Проверим синтаксис
print("\n🧪 Проверка синтаксиса admin.py:")
import subprocess
result = subprocess.run(["python3", "-m", "py_compile", "admin.py"], 
                       capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Синтаксис правильный")
else:
    print("❌ Синтаксическая ошибка:")
    print(result.stderr[:200])
