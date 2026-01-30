#!/usr/bin/env python3
"""
Улучшение функции show_product
Создан: 2026-01-30 15:05
"""
import re

def improve_show_product():
    with open('handlers.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим блок с отправкой фото
    pattern = r'(# Проверяем есть ли изображение.*?)await callback\.answer\("❌ Ошибка загрузки товара", show_alert=True\)'
    
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ Не найден блок show_product")
        return False
    
    old_block = match.group(1)
    
    # Новый улучшенный блок
    new_block = '''# Проверяем есть ли изображение
        if product.get('image_url'):
            try:
                # Удаляем предыдущее сообщение
                await callback.message.delete()
                # Отправляем новое сообщение с фото
                await callback.bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=product['image_url'],
                    caption=caption,
                    reply_markup=keyboard
                )
            except Exception as photo_error:
                logger.error(f"Ошибка отправки фото: {photo_error}")
                # Если не удалось отправить фото, отправляем текст
                await callback.message.edit_text(caption, reply_markup=keyboard)
        else:
            # Если нет изображения, редактируем текст как обычно
            await callback.message.edit_text(caption, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка показа товара: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)'''
    
    # Заменяем
    new_content = content.replace(old_block, new_block)
    
    with open('handlers.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Функция show_product улучшена")
    return True

if __name__ == "__main__":
    # Просто проверяем что функция существует
    with open('handlers.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'send_photo' in content and 'edit_caption' in content:
        print("✅ Функции уже содержат необходимые исправления")
    else:
        print("⚠️  Рекомендуется проверить вручную")
