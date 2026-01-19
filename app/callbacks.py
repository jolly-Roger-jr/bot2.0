# app/callbacks.py - Callback данные для Barkery_bot

class CB:
    """Константы для callback данных"""
    
    # Категории
    CATEGORY = "category"
    
    # Товары
    PRODUCT = "product"
    
    # Количество
    QTY = "qty"
    
    # Корзина
    CART_ADD = "cart:add"
    CART_SHOW = "cart:show"
    CART_CLEAR = "cart:clear"
    
    # Заказы
    ORDER_CONFIRM = "order:confirm"
    ORDER_CANCEL = "order:cancel"
    
    # Админка
    ADMIN_BACK = "admin:back"
    ADMIN_PRODUCTS = "admin:products"
    ADMIN_STOCK = "admin:stock"
    ADMIN_ORDERS = "admin:orders"
    ADMIN_BACKUPS = "admin:backups"
