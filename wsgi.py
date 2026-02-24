"""
WSGI точка входа для PythonAnywhere
Простая обертка для barkery_pythonanywhere.py
"""
import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем приложение
from barkery_pythonanywhere import application

# PythonAnywhere ищет переменную 'application'
# application уже инициализирована в barkery_pythonanywhere.py
