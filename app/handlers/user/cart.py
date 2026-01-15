import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from app.keyboards.user import categories_keyboard, products_keyboard, quantity_keyboard
from app.db.engine import SessionLocal
from app.db.models import Product, Category, CartItem, User
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = Router()

# -------------------------------
# Выбор категории
# -------------------------------
@router.callback_query(F.data.startswith("category:"))
async def category_callback(query: CallbackQuery):
    category_name = query.data.split(":", 1)[1]
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
    kb = quantity_keyboard(product_name, category_name)
    await query.message.edit_text(
        f"Вы выбрали товар: {product_name}\nВыберите количество:",
        reply_markup=kb
    )

# -------------------------------
# Обработка кнопок + и -
# -------------------------------
@router.callback_query(F.data.startswith("qty:"))
async def quantity_callback(query: CallbackQuery):
    try:
        if query.data == "qty:noop":
            await query.answer(cache_time=1)
            return

        _, product_name, action, category_name = query.data.split(":")

        current_qty = int(query.message.reply_markup.inline_keyboard[0][1].text)

        if action == "inc":
            current_qty += 1
        elif action == "dec" and current_qty > 1:
            current_qty -= 1

        # Изменяем клавиатуру только если количество реально изменилось
        old_qty = int(query.message.reply_markup.inline_keyboard[0][1].text)
        if old_qty != current_qty:
            kb = quantity_keyboard(product_name, category_name, current_qty)
            await query.message.edit_reply_markup(reply_markup=kb)

        await query.answer()

    except Exception as e:
        logger.error("Error in quantity_callback: %s", e)
        await query.answer("Произошла ошибка", show_alert=True)

# -------------------------------
# Назад к категориям
# -------------------------------
@router.callback_query(F.data == "back:categories")
async def back_to_categories_callback(query: CallbackQuery):
    kb = await categories_keyboard()
    await query.message.edit_text("Выберите категорию:", reply_markup=kb)

# -------------------------------
# Назад к товарам
# -------------------------------
@router.callback_query(F.data.startswith("back:category:"))
async def back_to_products_callback(query: CallbackQuery):
    category_name = query.data.split(":", 2)[2]
    kb = await products_keyboard(category_name)
    if not kb:
        await query.answer("В этой категории пока нет товаров", show_alert=True)
        return
    await query.message.edit_text(f"Товары в категории {category_name}:", reply_markup=kb)

# -------------------------------
# Добавление товара в корзину
# -------------------------------
@router.callback_query(F.data.startswith("cart:add:"))
async def add_to_cart_callback(query: CallbackQuery):
    try:
        _, _, product_name, qty, category_name = query.data.split(":")
        qty = int(qty)
        user_id = query.from_user.id

        async with SessionLocal() as session:
            # Получаем пользователя или создаём нового
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(telegram_id=user_id)
                session.add(user)
                await session.commit()

            # Получаем продукт
            result = await session.execute(select(Product).where(Product.name == product_name))
            product = result.scalar_one()

            # Проверяем запись в корзине
            result = await session.execute(
                select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product.id)
            )
            cart_item = result.scalar_one_or_none()

            if cart_item:
                cart_item.quantity += qty
            else:
                cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=qty)
                session.add(cart_item)

            await session.commit()

        await query.answer(f"{product_name} ({qty} шт.) добавлено в корзину", show_alert=True)
        logger.info("User %s added %sx %s to cart in category %s", user_id, qty, product_name, category_name)

    except Exception as e:
        logger.error("Error in add_to_cart_callback: %s", e)
        await query.answer("Произошла ошибка", show_alert=True)

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
        text += f"{item.product.name}: {item.quantity}\n"

    await message.answer(text)