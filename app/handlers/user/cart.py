import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from app.db.engine import SessionLocal
from app.db.models import User, Product, CartItem
from app.services import catalog
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = Router()

# -------------------------------
# Асинхронные клавиатуры
# -------------------------------
async def categories_keyboard() -> InlineKeyboardMarkup:
    cats = await catalog.get_categories()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=cat, callback_data=f"category:{cat}")] for cat in cats]
    )
    return kb

async def products_keyboard(category_name: str) -> InlineKeyboardMarkup | None:
    products = await catalog.get_products(category_name)
    if not products:
        return None
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{p['name']} — {p['price']} ₽\n{p['description']}",
                    callback_data=f"product:{p['name']}:{category_name}"
                )
            ] for p in products
        ]
    )
    return kb

def quantity_keyboard(product_name: str, category_name: str, price: float, current_qty: int = 1) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="−", callback_data=f"qty:{product_name}:dec:{category_name}"),
                InlineKeyboardButton(text=str(current_qty), callback_data="qty:noop"),
                InlineKeyboardButton(text="+", callback_data=f"qty:{product_name}:inc:{category_name}")
            ],
            [
                InlineKeyboardButton(
                    text=f"Добавить в корзину ({current_qty} x {price} ₽ = {current_qty*price} ₽)",
                    callback_data=f"cart:add:{product_name}:{current_qty}:{category_name}"
                ),
                InlineKeyboardButton(
                    text="⬅ Назад к товарам",
                    callback_data=f"back:category:{category_name}"
                )
            ],
            [
                InlineKeyboardButton(text="⬅ Назад к категориям", callback_data="back:categories")
            ]
        ]
    )

# -------------------------------
# Выбор категории
# -------------------------------
@router.callback_query(F.data.startswith("category:"))
async def category_callback(query: CallbackQuery):
    category_name = query.data.split(":", 1)[1]
    logger.info("CATEGORY click: %s | user=%s", category_name, query.from_user.id)

    kb = await products_keyboard(category_name)
    if not kb:
        await query.answer("В этой категории пока нет товаров", show_alert=True)
        return

    await query.message.edit_text(f"Товары в категории {category_name}:", reply_markup=kb)

# -------------------------------
# Выбор товара
# -------------------------------
@router.callback_query(F.data.startswith("product:"))
async def product_callback(query: CallbackQuery):
    _, product_name, category_name = query.data.split(":")
    logger.info("PRODUCT click: %s | category=%s | user=%s", product_name, category_name, query.from_user.id)

    # Получаем цену для quantity_keyboard
    products = await catalog.get_products(category_name)
    product = next((p for p in products if p["name"] == product_name), None)
    if not product:
        await query.answer("Ошибка: товар не найден", show_alert=True)
        return

    kb = quantity_keyboard(product_name, category_name, price=product["price"], current_qty=1)
    await query.message.edit_text(
        f"Вы выбрали товар: {product_name}\nЦена: {product['price']} ₽\n{product['description']}\nВыберите количество:",
        reply_markup=kb
    )

# -------------------------------
# Кнопки + и -
# -------------------------------
@router.callback_query(F.data.startswith("qty:"))
async def quantity_callback(query: CallbackQuery):
    logger.info("QTY raw: %s", query.data)
    if query.data == "qty:noop":
        await query.answer(cache_time=1)
        return

    try:
        _, product_name, action, category_name = query.data.split(":")
        # Получаем цену для обновления кнопки
        products = await catalog.get_products(category_name)
        product = next((p for p in products if p["name"] == product_name), None)
        if not product:
            await query.answer("Ошибка: товар не найден", show_alert=True)
            return
        price = product["price"]

        old_qty = int(query.message.reply_markup.inline_keyboard[0][1].text)
        new_qty = old_qty

        if action == "inc":
            new_qty += 1
        elif action == "dec" and old_qty > 1:
            new_qty -= 1

        if new_qty != old_qty:
            kb = quantity_keyboard(product_name, category_name, price, current_qty=new_qty)
            await query.message.edit_reply_markup(reply_markup=kb)

        await query.answer()
        logger.info("QTY updated: %s %s -> %s | user=%s", product_name, old_qty, new_qty, query.from_user.id)

    except Exception:
        logger.exception("QTY ERROR")
        await query.answer("Ошибка", show_alert=True)

# -------------------------------
# Добавление в корзину
# -------------------------------
@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart_callback(query: CallbackQuery):
    logger.info("ADD TO CART raw: %s", query.data)
    try:
        _, _, product_name, qty_str, category_name = query.data.split(":")
        qty = int(qty_str)
        user_id = query.from_user.id
    except Exception:
        logger.exception("ADD TO CART PARSE ERROR")
        await query.answer("Ошибка", show_alert=True)
        return

    try:
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(telegram_id=user_id)
                session.add(user)
                await session.commit()

            result = await session.execute(select(Product).where(Product.name == product_name))
            product = result.scalar_one()

            result = await session.execute(
                select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id)
            )
            cart_item = result.scalar_one_or_none()

            if cart_item:
                cart_item.quantity += qty
            else:
                session.add(CartItem(user_id=user.id, product_id=product.id, quantity=qty))

            await session.commit()

        await query.answer(f"{product_name} ({qty} шт.) добавлено в корзину", show_alert=True)
        logger.info("User %s added %sx %s to cart in category %s", user_id, qty, product_name, category_name)

    except Exception:
        logger.exception("ADD TO CART ERROR")
        await query.answer("Ошибка", show_alert=True)

# -------------------------------
# Просмотр корзины
# -------------------------------
@router.message(F.text == "/cart")
async def show_cart(message: Message):
    user_id = message.from_user.id
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Ваша корзина пуста.")
            return

        result = await session.execute(select(CartItem).where(CartItem.user_id == user.id))
        items = result.scalars().all()

    if not items:
        await message.answer("Ваша корзина пуста.")
        return

    text = "Ваша корзина:\n"
    for item in items:
        total = float(item.product.price) * item.quantity
        text += f"{item.product.name}: {item.quantity} x {float(item.product.price)} ₽ = {total} ₽\n"

    await message.answer(text)