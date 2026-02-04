#!/bin/bash
# Обновляем обработчик admin_category_products_handler для получения unit_type
sed -i '/admin_category_products_handler/,/await callback.answer()/ {
    /products_list = \[/ {
        n
        n
        n
        n
        n
        n
        n
        n
        n
        n
        a\                "unit_type": p.unit_type,
    }
}' admin.py
