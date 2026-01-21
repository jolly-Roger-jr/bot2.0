# app/handlers/user/catalog.py - ЦЕНТРИРОВАННАЯ ВЕРСИЯ
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.methods import DeleteMessage

from app.services.catalog import get_categories, get_products_by_category, get_product
from app.services.cart import get_cart_summary, get_cart_items
from app.keyboards.user import products_keyboard, product_detail_keyboard

logger = logging.getLogger(__name__)
router = Router()


def create_centered_text(title: str, content: str = "") -> str:
    """Создание центрированного текста через пробелы"""
    centered_title = f"<pre>   {title}   </pre>\n\n"

    if content:
        lines = content.split('\n')
        centered_content = ""
        for line in lines:
            if line.strip():
                centered_content += f"   {line.strip()}\n"
            else:
                centered_content += "\n"
        return f"{centered_title}{centered_content}"

    return centered_title


async def clean_chat(callback: CallbackQuery):
    """Очистка предыдущих сообщений"""
    try:
        await callback.message.delete()
    except:
        pass


@router.callback_query(F.data.startswith("category:"))
async def show_products(callback: CallbackQuery):
    """Показ товаров категории с центрированием"""
    try:
        await clean_chat(callback)

        category = callback.data.split(":", 1)[1]
        products = await get_products_by_category(category)

        if not products:
            await callback.message.answer(
                create_centered_text(
                    f"📭 {category}",
                    "В этой категории\n"
                    "пока нет товаров."
                ),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        cart_info = await get_cart_summary(callback.from_user.id)
        keyboard = products_keyboard(products, category, cart_info=cart_info)

        await callback.message.answer(
            create_centered_text(
                f"📦 {category}",
                "Выберите вкусняшку\n"
                "для вашего питомца:"
            ),
            parse_mode="HTML",
            reply_markup=keyboard
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка загрузки", show_alert=True)


@router.callback_query(F.data.startswith("product_detail:"))
async def show_product_detail(callback: CallbackQuery):
    """Показ карточки товара с центрированием - всегда сбрасываем счетчик к 0"""
    try:
        await clean_chat(callback)

        parts = callback.data.split(":")
        if len(parts) != 3:
            await callback.answer("❌ Ошибка", show_alert=True)
            return

        product_id_str, category = parts[1], parts[2]
        product_id = int(product_id_str)

        product = await get_product(product_id)
        if not product:
            await callback.answer("❌ Товар не найден", show_alert=True)
            return

        if not product.available or product.stock_grams <= 0:
            await callback.message.answer(
                create_centered_text(
                    f"⏳ {product.name}",
                    "Этот товар временно\n"
                    "закончился.\n\n"
                    "Скоро пополним запасы! 🐾"
                ),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        # 🔥 ВАЖНО: СБРАСЫВАЕМ СЧЕТЧИК К 0 ПРИ КАЖДОМ ВХОДЕ
        in_cart_qty = 0

        # Формируем центрированный текст
        description = product.description if product.description else ""
        text = create_centered_text(
            f"🦴 {product.name}",
            f"{description}\n\n"
            f"💰 Цена: {product.price} RSD/100г\n"
            f"📦 В наличии: {product.stock_grams}г\n\n"
            f"Выберите количество:"
        )

        # Клавиатура с нулевым счетчиком
        keyboard = product_detail_keyboard(
            product_id=product.id,
            category=category,
            price=product.price,
            in_cart_qty=in_cart_qty,  # Всегда 0 при входе
            stock_grams=product.stock_grams
        )

        # Отправляем с изображением или без
        if product.image_url:
            try:
                await callback.message.answer_photo(
                    photo=product.image_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            except:
                # Если не удалось отправить фото, отправляем текст
                await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.answer("❌ Ошибка загрузки товара", show_alert=True)


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories_handler(callback: CallbackQuery):
    """Возврат к категориям с очисткой"""
    try:
        await clean_chat(callback)

        # Имитируем команду /start
        from app.handlers.user.start import start
        await start(callback.message)

    except Exception as e:
        logger.error(f"Ошибка возврата: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(F.text == "/catalog")
async def catalog_command(message: Message):
    """Команда /catalog как альтернатива"""
    try:
        categories = await get_categories()

        if not categories:
            await message.answer(
                create_centered_text(
                    "📦 Каталог",
                    "Категории товаров\n"
                    "пока не добавлены."
                ),
                parse_mode="HTML"
            )
            return

        cart_info = await get_cart_summary(message.from_user.id)
        keyboard = products_keyboard([], "", cart_info=cart_info)

        await message.answer(
            create_centered_text(
                "📦 Каталог",
                "Используйте кнопки выше\n"
                "для выбора категории."
            ),
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка в /catalog: {e}")
        await message.answer("❌ Ошибка загрузки каталога")