# app/handlers/user/start.py - ПОЛНАЯ ВЕРСИЯ С РОУТЕРОМ

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
import logging

from app.services.catalog import get_categories
from app.services.cart import get_cart_summary
from app.keyboards.user import categories_keyboard

logger = logging.getLogger(__name__)
router = Router()


def create_welcome_message() -> str:
    """Создание приветственного сообщения"""
    return (
        "🐶 *Добро пожаловать в Barkery!* 🐾\n\n"
        "Мы рады приветствовать вас в нашем магазине\n"
        "натуральных сушеных лакомств для собак!\n\n"
        "*Наши преимущества:*\n"
        "✅ Натуральные ингредиенты\n"
        "✅ Без консервантов и добавок\n"
        "✅ Свежие продукты каждый день\n"
        "✅ Доставка по Белграду\n\n"
        "Выберите категорию лакомств:"
    )


@router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    try:
        # Получаем категории и информацию о корзине
        categories = await get_categories()
        cart_info = await get_cart_summary(message.from_user.id)

        if not categories:
            await message.answer(
                "🐾 *Barkery* 🐶\n\n"
                "К сожалению, категории товаров пока не добавлены.\n"
                "Обратитесь к администратору.",
                parse_mode="Markdown"
            )
            return

        await message.answer(
            create_welcome_message(),
            parse_mode="Markdown",
            reply_markup=categories_keyboard(categories, message.from_user.id, cart_info)
        )

        logger.info(f"Новый пользователь: {message.from_user.id} - {message.from_user.username}")

    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке каталога.\n"
            "Пожалуйста, попробуйте позже."
        )


@router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "*🐾 Помощь по Barkery Bot* 🐶\n\n"
        "*Основные команды:*\n"
        "• /start - Главное меню\n"
        "• /help - Эта справка\n"
        "• /cart - Показать корзину\n"
        "• /catalog - Открыть каталог\n\n"
        "*Как сделать заказ:*\n"
        "1. Выберите категорию товаров\n"
        "2. Выберите товар и количество\n"
        "3. Добавьте в корзину\n"
        "4. Перейдите в корзину и оформите заказ\n\n"
        "*Контакты:*\n"
        "• Вопросы и поддержка: @barkery_support\n"
        "• Адрес: Белград, Сербия\n"
        "• Часы работы: 24/7\n\n"
        "Приятных покупок! 🦴"
    )

    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("about"))
async def about_command(message: Message):
    """Обработчик команды /about"""
    about_text = (
        "*🐕 О Barkery* 🦴\n\n"
        "*Barkery* - это магазин натуральных сушеных\n"
        "лакомств для собак в Белграде, Сербия.\n\n"
        "*Наша миссия:*\n"
        "Дарить радость и здоровье вашим питомцам\n"
        "с помощью натуральных и полезных угощений!\n\n"
        "*Особенности:*\n"
        "• Только натуральные ингредиенты\n"
        "• Сушка без химикатов\n"
        "• Свежесть гарантирована\n"
        "• Доставка 24/7\n\n"
        "Мы любим собак и заботимся об их здоровье! 🐾"
    )

    await message.answer(about_text, parse_mode="Markdown")


@router.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message):
    """Обработчик кнопки 'Главное меню'"""
    await start_command(message)


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    """Обработчик callback 'Главное меню'"""
    await start_command(callback.message)
    await callback.answer()


@router.message(F.text == "📦 Каталог")
async def catalog_menu(message: Message):
    """Обработчик кнопки 'Каталог'"""
    # Просто вызываем start, который покажет категории
    await start_command(message)


@router.callback_query(F.data == "catalog")
async def catalog_callback(callback: CallbackQuery):
    """Обработчик callback 'Каталог'"""
    await start_command(callback.message)
    await callback.answer()