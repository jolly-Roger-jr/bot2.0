# app/handlers/user/__init__.py
"""
User handlers - только объявление роутера.
Все импорты вынесены в app/handlers/__init__.py
"""

from aiogram import Router

# Создаем единый роутер для пользовательской части
router = Router()

# НИКАКИХ импортов здесь! Они вызывают циклические зависимости.
# Все импорты будут в главном app/handlers/__init__.py

__all__ = ['router']