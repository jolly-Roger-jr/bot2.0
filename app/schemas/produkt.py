from dataclasses import dataclass
from app.models.product import Product

@dataclass
class ProductDTO:
    id: int
    name: str
    description: str
    price: float

    @classmethod
    def from_orm(cls, product: Product) -> "ProductDTO":
        return cls(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
        )