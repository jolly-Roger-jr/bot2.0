from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services import catalog

# Асинхронная клавиатура категорий
async def categories_keyboard() -> InlineKeyboardMarkup:
    cats = await catalog.get_categories()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"category:{cat}")]
            for cat in cats
        ]
    )
    return kb

# Асинхронная клавиатура товаров
async def products_keyboard(category: str) -> InlineKeyboardMarkup | None:
    products = await catalog.get_products(category)
    if not products:
        return None
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=p, callback_data=f"product:{p}:{category}")]
            for p in products
        ]
    )
    return kb

# Синхронная клавиатура выбора количества
def quantity_keyboard(product: str, category: str, current_qty: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="−", callback_data=f"qty:{product}:dec:{category}"),
                InlineKeyboardButton(text=str(current_qty), callback_data="qty:noop"),
                InlineKeyboardButton(text="+", callback_data=f"qty:{product}:inc:{category}")
            ],
            [
                InlineKeyboardButton(
                    text="Добавить в корзину",
                    callback_data=f"cart:add:{product}:{current_qty}:{category}"
                ),
                InlineKeyboardButton(
                    text="⬅ Назад к товарам",
                    callback_data=f"back:category:{category}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад к категориям",
                    callback_data="back:categories"
                )
            ]
        ]
    )