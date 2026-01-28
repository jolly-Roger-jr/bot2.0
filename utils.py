"""
Вспомогательные функции
"""

def format_price(price: float) -> str:
    """Форматирование цены"""
    return f"{price:.0f} RSD"


def format_quantity(grams: int) -> str:
    """Форматирование количества"""
    if grams >= 1000:
        kg = grams / 1000
        return f"{kg:.1f} кг"
    return f"{grams} г"


def create_centered_text(title: str, content: str = "") -> str:
    """Создание центрированного текста (HTML)"""
    centered_title = f"<pre>   {title}   </pre>\n\n"
    
    if not content:
        return centered_title
    
    lines = content.strip().split('\n')
    centered_content = ""
    for line in lines:
        if line.strip():
            centered_content += f"   {line.strip()}\n"
        else:
            centered_content += "\n"
    
    return f"{centered_title}{centered_content}"


def validate_phone(phone: str) -> bool:
    """Проверка номера телефона"""
    # Простая проверка для сербских номеров
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+", "")
    
    # Сербские номера: начинаются с 381 или 0
    if phone.startswith("381"):
        return len(phone) >= 9  # 381 + номер
    elif phone.startswith("0"):
        return len(phone) >= 9  # 0 + номер
    else:
        return len(phone) >= 6  # Минимум 6 цифр для международных


def validate_address(address: str) -> bool:
    """Проверка адреса"""
    address = address.strip()
    # Адрес должен содержать улицу и город
    return len(address) >= 10 and any(word in address.lower() for word in ["ул", "улица", "street", "st"])
