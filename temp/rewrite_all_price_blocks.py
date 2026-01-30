with open('../handlers.py', 'r') as f:
    content = f.read()

# Найдем все блоки с проблемными price_display
import re

# Функция для исправления одного блока
def fix_price_block(match):
    block = match.group(0)
    # Исправляем price_display строки
    block = re.sub(
        r'price_display = f"💰 Цена: \{product\[\'price\'\]\} RSD/100г\n"',
        'price_display = f"💰 Цена: {product[\'price\']} RSD/100г\\n"',
        block
    )
    block = re.sub(
        r'price_display = f"💰 Цена: \{product\[\'price\'\]\} RSD/шт\n"',
        'price_display = f"💰 Цена: {product[\'price\']} RSD/шт\\n"',
        block
    )
    return block

# Применяем ко всем блокам, содержащим price_display
# Ищем более широкий контекст
pattern = r'(\s*if product\.get\(\'unit_type\'.*?price_display = f".*?\n\s*(?:f"?|else))'
content = re.sub(pattern, fix_price_block, content, flags=re.DOTALL)

# Также исправим строки с вложенными кавычками
content = re.sub(
    r'f"📦 В наличии: \{product\[\'stock\'\]\}\{"г" if product\.get\("unit_type", "grams"\) == "grams" else "шт"\}\\n"',
    'f"📦 В наличии: {product[\'stock\']}{\'г\' if product.get(\"unit_type\", \"grams\") == \"grams\" else \"шт\"}\\n"',
    content
)

with open('../handlers.py', 'w') as f:
    f.write(content)
print("Переписали проблемные блоки")

# Проверка
try:
    exec(open('../handlers.py').read())
    print("✅ handlers.py - синтаксис OK")
except SyntaxError as e:
    print(f"❌ handlers.py - ошибка: {e}")
    # Покажем проблемное место
    import traceback
    traceback.print_exc()
