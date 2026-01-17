from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.services import catalog
from app.keyboards.user import products_keyboard, quantity_keyboard
from app.callbacks import CB

router = Router()


@router.callback_query(F.data.startswith(CB.CATEGORY))
async def show_products(callback: CallbackQuery):
    _, category = callback.data.split(":", 1)
    products = await catalog.get_products_by_category(category)

    await callback.message.edit_text(
        f"📦 {category}",
        reply_markup=products_keyboard(products, category)
    )


@router.callback_query(F.data.startswith(CB.PRODUCT))
async def show_quantity(callback: CallbackQuery):
    _, product_id, category = callback.data.split(":", 2)
    product = await catalog.get_product(int(product_id))

    await callback.message.edit_text(
        f"{product.name}\n{product.description}\nЦена: {product.price} RSD",
        reply_markup=quantity_keyboard(product.id, category, product.price)
    )