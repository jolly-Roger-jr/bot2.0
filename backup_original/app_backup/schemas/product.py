from dataclasses import dataclass
from app.db.models import Product


@dataclass
class ProductDTO:
    id: int
    name: str
    description: str
    price: float
    available: bool  # ДОБАВЛЕНО
    stock_grams: int  # ДОБАВЛЕНО
    image_url: str | None  # ДОБАВЛЕНО

    @classmethod
    def from_orm(cls, product: Product) -> "ProductDTO":
        # ✅ Обрабатываем возможные None значения
        description = product.description if product.description else ""
        image_url = product.image_url if product.image_url else ""

        return cls(
            id=product.id,
            name=product.name,
            description=description,
            price=float(product.price),  # ✅ Явно преобразуем в float
            available=bool(product.available),  # ✅ Добавлено
            stock_grams=int(product.stock_grams),  # ✅ Добавлено
            image_url=image_url  # ✅ Добавлено
        )