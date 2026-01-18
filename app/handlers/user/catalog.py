from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.services import catalog
from app.keyboards.user import products_keyboard, quantity_keyboard
from app.callbacks import CB

router = Router()


# app/handlers/user/catalog.py - ОБНОВИТЬ ФУНКЦИЮ show_products

@router.callback_query(F.data.startswith(CB.CATEGORY))
async def show_products(callback: CallbackQuery):
    _, category = callback.data.split(":", 1)

    if category == "__back__":
        return

    products = await catalog.get_products_by_category(category)

    if not products:
        await callback.message.edit_text(
            f"📦 {category}\n\n"
            f"В этой категории пока нет товаров.",
            reply_markup=products_keyboard([], category)
        )
        return

    # Фильтруем только доступные товары
    available_products = []
    unavailable_products = []

    for product in products:
        if product.available and product.stock_grams > 0:
            available_products.append(product)
        else:
            unavailable_products.append(product)

    text = f"📦 {category}\n"

    if unavailable_products:
        text += f"\n⚠️ {len(unavailable_products)} товаров временно недоступно"

    await callback.message.edit_text(
        text,
        reply_markup=products_keyboard(available_products, category, show_unavailable=True)
    )

@router.callback_query(F.data.startswith(CB.PRODUCT))
async def show_quantity(callback: CallbackQuery):
    _, product_id, category = callback.data.split(":", 2)
    product = await catalog.get_product(int(product_id))

    await callback.message.edit_text(
        f"{product.name}\n{product.description}\nЦена: {product.price} RSD",
        reply_markup=quantity_keyboard(product.id, category, product.price)
    )


@router.callback_query(F.data == "back_to_categories")
async def handle_back_to_categories(callback: CallbackQuery):
    from app.services import catalog as cat_service
    categories = await cat_service.get_categories()
    from app.keyboards.user import categories_keyboard

    await callback.message.edit_text(
        "🐶 Barkery Shop\nВыберите категорию:",
        reply_markup=categories_keyboard(categories)
    )
    await callback.answer()


# app/handlers/user/catalog.py - ДОБАВИТЬ ОБРАБОТЧИК

@router.callback_query(F.data.startswith("product:unavailable:"))
async def show_unavailable_product_info(callback: CallbackQuery):
    """Показать информацию о недоступном товаре"""
    product_id = int(callback.data.split(":")[2])

    from app.services.catalog import get_product
    product = await get_product(product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    text = f"❌ *{product.name}*\n\n"

    if not product.available:
        text += "Товар временно недоступен.\n"
        text += "Возможно, он снят с продажи или находится на переоформлении.\n\n"
    elif product.stock_grams <= 0:
        text += "Товар закончился.\n"
        text += "Ожидайте поступления в ближайшее время.\n\n"

    text += f"Цена: {product.price} RSD/100г\n"

    if product.description:
        text += f"\n{product.description}"

    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()