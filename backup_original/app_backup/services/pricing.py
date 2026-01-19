from app.db.models import CartItem


class PricingService:
    @staticmethod
    def item_total(item: CartItem) -> float:
        return float(item.product.price) * item.quantity

    @staticmethod
    def format_rsd(value: float) -> str:
        return f"{int(value)} RSD"