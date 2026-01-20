# app/handlers/user/catalog.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
import logging

from app.services.catalog import get_categories, get_products_by_category, get_product
from app.services.cart import get_cart_summary, get_cart_items
from app.keyboards.user import products_keyboard, product_detail_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("category:"))
async def show_products(callback: CallbackQuery):
    """Показать товары выбранной категории"""
    try:
        category = callback.data.split(":", 1)[1]
        logger.info(f"📦 Пользователь выбрал категорию: {category}")

        products = await get_products_by_category(category)

        if not products:
            await callback.message.answer(
                f"📭 В категории '{category}' пока нет товаров",
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        cart_info = await get_cart_summary(callback.from_user.id)

        text = f"📦 *{category}*\n\n"
        text += "Выберите товар:\n"

        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=products_keyboard(
                products=products,
                category=category,
                show_unavailable=False,
                user_id=callback.from_user.id,
                cart_info=cart_info
            )
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе товаров: {e}")
        await callback.answer("❌ Ошибка загрузки товаров", show_alert=True)


@router.callback_query(F.data.startswith("product_detail:"))
async def show_product_detail(callback: CallbackQuery):
    """Показать детали товара с правильными кнопками по ТЗ"""
    try:
        parts = callback.data.split(":")

        if len(parts) != 3:
            await callback.answer("❌ Ошибка формата", show_alert=True)
            return

        _, product_id_str, category = parts

        try:
            product_id = int(product_id_str)
        except ValueError:
            await callback.answer("❌ Ошибка в данных товара", show_alert=True)
            return

        product = await get_product(product_id)

        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        if not product.available or product.stock_grams <= 0:
            await callback.message.answer(
                f"❌ *{product.name}*\n\n"
                f"Этот товар временно недоступен.\n"
                f"Попробуйте другие товары.",
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Проверяем, есть ли товар в корзине
        cart_items = await get_cart_items(callback.from_user.id)
        in_cart_qty = 0

        for item in cart_items:
            if item.product_id == product_id:
                in_cart_qty = item.quantity
                break

        # Формируем текст
        text = f"*{product.name}*\n\n"

        if product.description:
            text += f"{product.description}\n\n"

        text += f"*Цена:* {product.price} RSD за 100 грамм\n"
        text += f"*В наличии:* {product.stock_grams} грамм\n"

        if in_cart_qty > 0:
            text += f"\n*В корзине:* {in_cart_qty} грамм"

        # Получаем клавиатуру согласно ТЗ
        keyboard = product_detail_keyboard(
            product_id=product.id,
            category=category,
            price=product.price,
            in_cart_qty=in_cart_qty,
            stock_grams=product.stock_grams
        )

        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Ошибка при показе товара: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    """Вернуться к списку категорий"""
    try:
        from app.handlers.user.start import start

        class FakeMessage:
            def __init__(self, callback):
                self.from_user = callback.from_user
                self.text = "/start"

            async def answer(self, *args, **kwargs):
                return await callback.message.answer(*args, **kwargs)

        await start(FakeMessage(callback))
        await callback.answer()
    except Exception as e:
        logger.error(f"❌ Ошибка возврата к категориям: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(Command("catalog"))
async def catalog_command(message: Message):
    """Команда /catalog - альтернативный вход в каталог"""
    from app.handlers.user.start import start
    await start(message)