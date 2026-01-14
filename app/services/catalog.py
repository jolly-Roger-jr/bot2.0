# app/services/catalog.py

CATEGORIES = ["Печенье", "Торты", "Пирожные"]

PRODUCTS = {
    "Печенье": ["Овсяное", "Шоколадное", "Имбирное"],
    "Торты": ["Медовый", "Шоколадный", "Наполеон"],
    "Пирожные": ["Эклер", "Картошка", "Птичье молоко"]
}

def get_categories():
    """Возвращает список категорий"""
    return CATEGORIES

def get_products(category: str):
    """Возвращает список товаров по категории"""
    return PRODUCTS.get(category, [])