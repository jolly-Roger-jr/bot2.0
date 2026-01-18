# app/bot_working.py - РАБОЧАЯ ВЕРСИЯ
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from app.config import settings
from app.db.engine import engine
from app.db.models import Base
from app.scheduler import start_scheduler, setup_backup_schedule

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def setup_database():
    """Настройка базы данных"""
    logger.info("Инициализация базы данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ База данных проверена/создана")


async def main():
    """Главная функция запуска бота"""

    # 1. Настройка БД
    await setup_database()

    # 2. Настройка планировщика
    logger.info("Настройка планировщика резервного копирования...")
    setup_backup_schedule()
    start_scheduler()
    logger.info("✅ Планировщик запущен")

    # 3. Инициализация бота и диспетчера
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # 4. Создаем главный роутер
    main_router = Router()

    # 5. Базовые команды
    @main_router.message(CommandStart())
    async def cmd_start(message: Message):
        """Главное меню"""
        await message.answer(
            "🐶 <b>Barkery Shop</b>\n\n"
            "Магазин натуральных сушеных собачьих лакомств.\n"
            "Используйте /menu для выбора категорий\n"
            "/cart - корзина\n"
            "/help - помощь",
            parse_mode="HTML"
        )

    @main_router.message(Command("help"))
    async def cmd_help(message: Message):
        """Помощь"""
        await message.answer(
            "ℹ️ <b>Помощь</b>\n\n"
            "/start - Главное меню\n"
            "/menu - Категории товаров\n"
            "/cart - Корзина\n"
            "/admin - Админ-панель (только для администратора)\n"
            "/help - Эта справка",
            parse_mode="HTML"
        )

    @main_router.message(Command("cart"))
    async def cmd_cart(message: Message):
        """Корзина"""
        from app.services.cart import get_cart_total
        result = await get_cart_total(message.from_user.id)

        if not result.get('success', False):
            await message.answer("🛒 Корзина пуста")
            return

        text = "🛒 *Ваша корзина:*\n\n"
        for item in result.get('items', []):
            if item.product:
                subtotal = item.product.price * item.quantity / 100
                text += f"• *{item.product.name}*\n"
                text += f"  {item.quantity}г × {item.product.price} RSD/100г = {int(subtotal)} RSD\n\n"

        text += f"*Итого:* {int(result.get('total', 0))} RSD"

        from app.keyboards.user import cart_keyboard
        await message.answer(text, parse_mode="Markdown", reply_markup=cart_keyboard())

    @main_router.message(Command("admin"))
    async def cmd_admin(message: Message):
        """Админ-панель"""
        if message.from_user.id != settings.admin_id:
            await message.answer("❌ У вас нет доступа к админ-панели")
            return

        from app.keyboards.admin import admin_menu
        await message.answer("⚙️ Админ-панель Barkery", reply_markup=admin_menu())

    logger.info("✅ Базовые команды зарегистрированы")

    # 6. РУЧНОЙ импорт и регистрация хендлеров (без использования роутеров)

    # user.catalog
    from app.handlers.user.catalog import router as catalog_router
    @main_router.callback_query(lambda c: c.data.startswith("category:"))
    async def handle_category(callback):
        from app.services import catalog as cat_service
        from app.keyboards.user import products_keyboard
        category = callback.data.split(":", 1)[1]
        products = await cat_service.get_products_by_category(category)
        text = f"📦 {category}\n\n" if products else f"📦 {category}\n\nНет товаров."
        await callback.message.edit_text(
            text,
            reply_markup=products_keyboard(products, category, show_unavailable=True)
        )
        await callback.answer()

    @main_router.callback_query(lambda c: c.data.startswith("product:"))
    async def handle_product(callback):
        from app.services.catalog import get_product
        from app.keyboards.user import quantity_keyboard
        parts = callback.data.split(":")
        if len(parts) >= 3:
            product_id = int(parts[1])
            category = parts[2]
            product = await get_product(product_id)
            if product and product.available and product.stock_grams > 0:
                await callback.message.edit_text(
                    f"<b>{product.name}</b>\n\n{product.description}\n\n"
                    f"💰 Цена: <b>{product.price} RSD/100г</b>\n"
                    f"📦 В наличии: <b>{product.stock_grams}г</b>",
                    parse_mode="HTML",
                    reply_markup=quantity_keyboard(product.id, category, product.price)
                )
            else:
                await callback.answer("❌ Товар недоступен", show_alert=True)
        await callback.answer()

    # user.qty
    @main_router.callback_query(lambda c: c.data.startswith("qty:"))
    async def handle_qty(callback):
        from app.keyboards.user import quantity_keyboard
        from app.services.catalog import get_product
        parts = callback.data.split(":")
        if len(parts) == 5:
            product_id = int(parts[1])
            action = parts[2]
            category = parts[3]
            current_qty = int(parts[4])

            new_qty = current_qty + 1 if action == "inc" else max(1, current_qty - 1)
            product = await get_product(product_id)

            if product:
                new_keyboard = quantity_keyboard(product_id, category, product.price, new_qty)
                await callback.message.edit_reply_markup(reply_markup=new_keyboard)
                await callback.answer(f"Количество: {new_qty}")

    # user.cart
    @main_router.callback_query(lambda c: c.data.startswith("cart:add:"))
    async def handle_cart_add(callback):
        from app.services.cart import add_to_cart
        parts = callback.data.split(":")
        if len(parts) == 5:
            product_id = int(parts[2])
            qty = int(parts[3])
            result = await add_to_cart(callback.from_user.id, product_id, qty)
            if result['success']:
                await callback.answer(f"✅ Добавлено {qty}г")
            else:
                await callback.answer(f"❌ {result.get('error', 'Ошибка')}", show_alert=True)

    # 7. Включаем главный роутер
    dp.include_router(main_router)

    # 8. Проверка
    msg_count = len(list(dp.message.handlers))
    cb_count = len(list(dp.callback_query.handlers))

    logger.info(f"📊 Хендлеров: {msg_count} сообщений, {cb_count} callback")

    if msg_count == 0:
        logger.error("❌ КРИТИЧЕСКАЯ ОШИБКА!")
        return

    # 9. Запуск
    logger.info(f"\n🚀 БОТ ЗАПУЩЕН!")
    logger.info(f"🤖 Admin ID: {settings.admin_id}")
    logger.info(f"📱 Отправьте /start в Telegram")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("⏹ Остановка")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        raise
    finally:
        from app.scheduler import stop_scheduler
        stop_scheduler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Фатальная ошибка: {e}")