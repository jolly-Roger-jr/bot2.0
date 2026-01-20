# app/handlers/user/start.py
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove

from app.services import catalog
from app.services.cart import get_cart_summary
from app.keyboards.user import categories_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def start(message: Message):
    """Обработчик команды /start - главное меню"""
    logger.info(f"🚀 /start вызван для пользователя {message.from_user.id}")

    try:
        # Получаем категории
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

        # Получаем информацию о корзине
        cart_info = await get_cart_summary(message.from_user.id)

        # Создаем клавиатуру
        keyboard = categories_keyboard(categories, message.from_user.id, cart_info)

        await message.answer(
            "🐶 <b>Barkery Shop</b>\n\n"
            "Магазин натуральных сушеных собачьих лакомств.\n"
            "Выберите категорию:",
            parse_mode="HTML",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await message.answer(
            "🐶 <b>Barkery Shop</b>\n\n"
            "Магазин натуральных сушеных собачьих лакомств.\n\n"
            "Команды:\n"
            "/start - главное меню\n"
            "/cart - корзина\n"
            "/help - помощь\n"
            "/admin - админ-панель\n\n"
            "<i>Работаем 24/7! 🐾</i>",
            parse_mode="HTML"
        )


@router.message(Command("help"))
async def help_command(message: Message):
    """Команда помощи"""
    help_text = (
        "🐶 <b>Barkery Shop - Помощь</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Главное меню\n"
        "/cart - Просмотр корзина\n"
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


@router.message(Command("test"))
async def test_command(message: Message):
    """Тестовая команда для проверки работы бота"""
    await message.answer(
        "✅ <b>Бот работает!</b>\n\n"
        "Это тестовое сообщение подтверждает, что бот отвечает на команды.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )