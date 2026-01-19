# app/handlers/user/start.py - ИСПРАВЛЕННАЯ ВЕРСИЯ

import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove

from app.services import catalog
from app.keyboards.user import categories_keyboard

logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    """Обработчик команды /start - главное меню"""
    logger.info(f"🚀 /start вызван для пользователя {message.from_user.id}")
    categories = await catalog.get_categories()

    if not categories:
        await message.answer(
            "🐶 <b>Добро пожаловать в Barkery Shop!</b>\n\n"
            "Магазин натуральных сушеных собачьих лакомств.\n\n"
            "К сожалению, категории товаров еще не добавлены.\n"
            "Администратор должен добавить товары через админ-панель.\n\n"
            "Для администрирования используйте /admin",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🐶 <b>Barkery Shop</b>\n\n"
        "Магазин натуральных сушеных собачьих лакомств.\n"
        "Выберите категорию:",
        parse_mode="HTML",
        reply_markup=categories_keyboard(categories)
    )


@router.message(Command("help"))
async def help_command(message: Message):
    """Команда помощи"""
    help_text = (
        "🐶 <b>Barkery Shop - Помощь</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Главное меню\n"
        "/cart - Просмотр корзины\n"
        "/help - Эта справка\n"
        "/test - Тест работы бота\n\n"

        "<b>Как сделать заказ:</b>\n"
        "1. Выберите категорию товаров\n"
        "2. Выберите товар\n"
        "3. Укажите количество и добавьте в корзину\n"
        "4. Перейдите в корзину (/cart)\n"
        "5. Оформите заказ\n\n"

        "<b>Для администратора:</b>\n"
        "/admin - Админ-панель\n\n"

        "<i>Работаем 24/7! 🐾</i>"
    )

    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("about"))
async def about_command(message: Message):
    """Информация о магазине"""
    about_text = (
        "🏪 <b>Barkery Shop</b>\n\n"
        "Интернет-магазин натуральных сушеных собачьих лакомств.\n\n"

        "<b>Наши преимущества:</b>\n"
        "✅ 100% натуральные продукты\n"
        "✅ Без консервантов и добавок\n"
        "✅ Доступно 24/7\n"
        "✅ Доставка по Сербии\n\n"

        "<b>Контакты:</b>\n"
        "📍 Сербия, Белград\n"
        "⏰ Работаем круглосуточно\n\n"

        "<i>Ваш питомец заслуживает лучшего! 🐕</i>"
    )

    await message.answer(about_text, parse_mode="HTML")


@router.message(Command("test"))
async def test_command(message: Message):
    """Тестовая команда для проверки работы бота"""
    await message.answer(
        "✅ <b>Бот работает!</b>\n\n"
        "Это тестовое сообщение подтверждает, что бот отвечает на команды.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("cart"))
async def cart_command(message: Message):
    """Прямая команда для корзины (дублирует функционал из cart.py)"""
    from app.services.cart import get_cart_total

    result = await get_cart_total(message.from_user.id)

    if not result.get('success', False):
        await message.answer("🛒 Корзина пуста")
        return

    items = result.get('items', [])
    total = result.get('total', 0)

    text = "🛒 *Ваша корзина:*\n\n"

    for item in items:
        if item.product:
            subtotal = item.product.price * item.quantity / 100
            text += f"• *{item.product.name}*\n"
            text += f"  {item.quantity}г × {item.product.price} RSD/100г = {int(subtotal)} RSD\n\n"

    text += f"*Итого:* {int(total)} RSD"

    from app.keyboards.user import cart_keyboard
    await message.answer(text, parse_mode="Markdown", reply_markup=cart_keyboard())