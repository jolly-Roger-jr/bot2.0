# app/keyboards/user.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def quantity_keyboard(
    product_id: int,
    product_name: str,
    category_name: str,
    price: float,
    current_qty: int = 1
) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора количества и добавления в корзину.
    Показывается условия: цена на единицу и итог.
    """
    total = current_qty * price
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="−",
                    callback_data=f"qty:{product_id}:dec:{category_name}"
                ),
                InlineKeyboardButton(
                    text=str(current_qty),
                    callback_data="qty:noop"
                ),
                InlineKeyboardButton(
                    text="+",
                    callback_data=f"qty:{product_id}:inc:{category_name}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=(
                        f"Добавить в корзину "
                        f"({current_qty} x {price} RSD = {total} RSD)"
                    ),
                    callback_data=f"cart:add:{product_id}:{current_qty}:{category_name}"
                ),
                InlineKeyboardButton(
                    text="⬅ Назад к товарам",
                    callback_data=f"back:category:{category_name}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад к категориям",
                    callback_data="back:categories"
                ),
            ],
        ]
    )
    return kb


async def categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопками категорий.
    Вход: список названий категорий.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=cat,
                    callback_data=f"category:{cat}"
                )
            ]
            for cat in categories
        ]
    )


async def products_keyboard(
    products: list[dict],
    category_name: str
) -> InlineKeyboardMarkup:
    """
    Клавиатура товаров данной категории.
    products: список словарей с keys=id,name,price,description
    """
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=(
                        f"{p['name']} — {p['price']} RSD\n"
                        f"{p['description']}"
                    ),
                    callback_data=f"product:{p['id']}:{category_name}"
                )
            ]
            for p in products
        ]
    )
    return kb