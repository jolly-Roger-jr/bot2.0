from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.services import catalog
from app.keyboards.user import products_keyboard, quantity_keyboard
from app.callbacks import CB

router = Router()


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

    # ВСЕ товары уже фильтруются в products_keyboard по их available/stock_grams
    # Убираем лишнюю фильтрацию здесь
    text = f"📦 {category}\n\n"

    # Считаем недоступные товары для информации
    unavailable_count = sum(1 for p in products if not (p.available and p.stock_grams > 0))

    if unavailable_count:
        text += f"⚠️ {unavailable_count} товаров временно недоступно\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=products_keyboard(products, category, show_unavailable=True)
    )


@router.callback_query(F.data.startswith(CB.PRODUCT))
async def show_quantity(callback: CallbackQuery):
    _, product_id, category = callback.data.split(":", 2)
    product = await catalog.get_product(int(product_id))

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    # Проверяем доступность товара
    if not product.available or product.stock_grams <= 0:
        await callback.answer("❌ Товар временно недоступен", show_alert=True)
        return

    await callback.message.edit_text(
        f"<b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"💰 Цена: <b>{product.price} RSD/100г</b>\n"
        f"📦 В наличии: <b>{product.stock_grams}г</b>",
        parse_mode="HTML",
        reply_markup=quantity_keyboard(product.id, category, product.price)
    )


@router.callback_query(F.data == "back_to_categories")
async def handle_back_to_categories(callback: CallbackQuery):
    from app.services import catalog as cat_service
    categories = await cat_service.get_categories()
    from app.keyboards.user import categories_keyboard

    await callback.message.edit_text(
        "🐶 <b>Barkery Shop</b>\n\nВыберите категорию:",
        parse_mode="HTML",
        reply_markup=categories_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:unavailable:"))
async def show_unavailable_product_info(callback: CallbackQuery):
    """Показать информацию о недоступном товаре"""
    product_id = int(callback.data.split(":")[2])

    from app.services.catalog import get_product
    product = await get_product(product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    text = f"❌ <b>{product.name}</b>\n\n"

    if not product.available:
        text += "Товар временно недоступен.\n"
        text += "Возможно, он снят с продажи или находится на переоформлении.\n\n"
    elif product.stock_grams <= 0:
        text += "Товар закончился.\n"
        text += "Ожидайте поступления в ближайшее время.\n\n"

    text += f"💰 Цена: <b>{product.price} RSD/100г</b>\n"

    if product.description:
        text += f"\n{product.description}"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()