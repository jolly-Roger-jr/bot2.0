import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from app.db.engine import SessionLocal
from app.db.models import User, Product, CartItem, Category
from app.keyboards.user import quantity_keyboard, categories_keyboard, products_keyboard
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = Router()

# -------------------------------
# Выбор категории
# -------------------------------
@router.callback_query(F.data.startswith("category:"))
async def category_callback(query: CallbackQuery):
    category_name = query.data.split(":", 1)[1]
    logger.info("CATEGORY click: %s | user=%s", category_name, query.from_user.id)

    # Получаем продукты этой категории
    async with SessionLocal() as session:
        result = await session.execute(
            select(Product.id, Product.name, Product.price, Product.description)
            .join(Category)
            .where(Category.name == category_name)
        )
        products = [
            {"id": row[0], "name": row[1], "price": float(row[2]), "description": row[3] or ""}
            for row in result.fetchall()
        ]

    if not products:
        await query.answer("В этой категории пока нет товаров", show_alert=True)
        return

    kb = await products_keyboard(products, category_name)
    await query.message.edit_text(f"Товары в категории {category_name}:", reply_markup=kb)

# -------------------------------
# Выбор товара
# -------------------------------
@router.callback_query(F.data.startswith("product:"))
async def product_callback(query: CallbackQuery):
    product_id, category_name = query.data.split(":")[1:]
    product_id = int(product_id)

    async with SessionLocal() as session:
        result = await session.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            await query.answer("Ошибка: товар не найден", show_alert=True)
            return

    kb = quantity_keyboard(product.id, product.name, category_name, price=float(product.price), current_qty=1)
    await query.message.edit_text(
        f"Вы выбрали товар: {product.name}\nЦена: {float(product.price)} RSD\n{product.description}\nВыберите количество:",
        reply_markup=kb
    )

# -------------------------------
# Кнопки + и -
# -------------------------------
@router.callback_query(F.data.startswith("qty:"))
async def qty_callback(query: CallbackQuery):
    if query.data == "qty:noop":
        await query.answer(cache_time=1)
        return

    try:
        product_id, action, category_name = query.data.split(":")[1:]
        product_id = int(product_id)

        async with SessionLocal() as session:
            result = await session.execute(select(Product).where(Product.id == product_id))
            product = result.scalar_one()

        old_qty = int(query.message.reply_markup.inline_keyboard[0][1].text)
        new_qty = old_qty
        if action == "inc":
            new_qty += 1
        elif action == "dec" and old_qty > 1:
            new_qty -= 1

        if new_qty != old_qty:
            kb = quantity_keyboard(product.id, product.name, category_name, price=float(product.price), current_qty=new_qty)
            await query.message.edit_reply_markup(reply_markup=kb)

        await query.answer()
        logger.info("QTY updated: %s %s -> %s | user=%s", product.name, old_qty, new_qty, query.from_user.id)

    except Exception:
        logger.exception("QTY ERROR")
        await query.answer("Ошибка", show_alert=True)

# -------------------------------
# Добавление в корзину
# -------------------------------
@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart_callback(query: CallbackQuery):
    try:
        _, _, product_id, qty_str, category_name = query.data.split(":")
        product_id, qty = int(product_id), int(qty_str)
        user_id = query.from_user.id

        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(telegram_id=user_id)
                session.add(user)
                await session.commit()

            result = await session.execute(select(Product).where(Product.id == product_id))
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

        await query.answer(f"{product.name} ({qty} шт.) добавлено в корзину", show_alert=True)
        logger.info("User %s added %sx %s to cart in category %s", user_id, qty, product.name, category_name)

    except Exception:
        logger.exception("ADD TO CART ERROR")
        await query.answer("Ошибка", show_alert=True)

# -------------------------------
# Назад к категориям
# -------------------------------
@router.callback_query(F.data == "back:categories")
async def back_to_categories_callback(query: CallbackQuery):
    async with SessionLocal() as session:
        result = await session.execute(select(Category.name))
        categories = [row[0] for row in result.fetchall()]
    kb = await categories_keyboard(categories)
    await query.message.edit_text("Выберите категорию:", reply_markup=kb)

# -------------------------------
# Назад к товарам
# -------------------------------
@router.callback_query(F.data.startswith("back:category:"))
async def back_to_products_callback(query: CallbackQuery):
    category_name = query.data.split(":", 2)[2]
    async with SessionLocal() as session:
        result = await session.execute(
            select(Product.id, Product.name, Product.price, Product.description)
            .join(Category)
            .where(Category.name == category_name)
        )
        products = [
            {"id": row[0], "name": row[1], "price": float(row[2]), "description": row[3] or ""}
            for row in result.fetchall()
        ]

    if not products:
        await query.answer("В этой категории пока нет товаров", show_alert=True)
        return

    kb = await products_keyboard(products, category_name)
    await query.message.edit_text(f"Товары в категории {category_name}:", reply_markup=kb)

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
        text += f"{item.product.name}: {item.quantity} x {float(item.product.price)} RSD = {total} RSD\n"

    await message.answer(text)