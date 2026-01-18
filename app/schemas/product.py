from dataclasses import dataclass
from app.db.models import Product


@dataclass
class ProductDTO:
    id: int
    name: str
    description: str
    price: float

    @classmethod
    def from_orm(cls, product: Product) -> "ProductDTO":
        # ✅ Обрабатываем возможные None значения
        description = product.description if product.description else ""

        return cls(
            id=product.id,
            name=product.name,
            description=description,
            price=float(product.price)  # ✅ Явно преобразуем в float
        )