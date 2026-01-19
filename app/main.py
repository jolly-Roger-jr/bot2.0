# app/main.py - ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import text

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск Barkery Bot...")

    # 1. Загружаем настройки
    from dotenv import load_dotenv
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    admin_id_str = os.getenv("ADMIN_ID", "0")

    if not token:
        logger.error("❌ ОШИБКА: BOT_TOKEN не найден!")
        return

    try:
        admin_id = int(admin_id_str)
    except ValueError:
        logger.error(f"❌ Неверный ADMIN_ID: '{admin_id_str}'")
        admin_id = 0

    # 2. Создаем бота и диспетчер
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())

    # ========== БАЗОВЫЕ ХЕНДЛЕРЫ ==========
    @dp.message(CommandStart())
    async def cmd_start(message: Message):
        """Обработчик /start"""
        try:
            from app.services.catalog import get_categories
            categories = await get_categories()

            if categories:
                from app.keyboards.user import categories_keyboard
                await message.answer(
                    "🐶 <b>Barkery Shop</b>\n\n"
                    "Магазин натуральных сушеных собачьих лакомств.\n"
                    "Выберите категорию:",
                    parse_mode="HTML",
                    reply_markup=categories_keyboard(categories)
                )
            else:
                await message.answer(
                    "🐶 <b>Barkery Shop</b>\n\n"
                    "Магазин натуральных сушеных собачьих лакомств.\n\n"
                    "Товары скоро появятся!\n"
                    "Администратор должен добавить товары через /admin",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Ошибка в /start: {e}")
            await message.answer(
                "🐶 <b>Barkery Shop</b>\n\n"
                "Магазин натуральных сушеных собачьих лакомств.\n\n"
                "Команды:\n"
                "/catalog - каталог товаров\n"
                "/cart - корзина\n"
                "/help - помощь\n"
                "/admin - админ-панель\n\n"
                "<i>Работаем 24/7! 🐾</i>",
                parse_mode="HTML"
            )

    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        help_text = (
            "🐶 <b>Barkery Shop - Помощь</b>\n\n"
            "<b>Основные команды:</b>\n"
            "/start - Главное меню\n"
            "/catalog - Каталог товаров\n"
            "/cart - Корзина\n"
            "/help - Эта справка\n\n"
            "<b>Как сделать заказ:</b>\n"
            "1. Выберите категорию товаров\n"
            "2. Выберите товар\n"
            "3. Укажите количество и добавьте в корзину\n"
            "4. Перейдите в корзину\n"
            "5. Оформите заказ\n\n"
            "<b>Для администратора:</b>\n"
            "/admin - Админ-панель\n"
            "/stock - Управление остатками\n"
            "/orders - Просмотр заказов\n"
            "/backup - Резервное копирование\n\n"
            "<i>Работаем 24/7! 🐾</i>"
        )
        await message.answer(help_text, parse_mode="HTML")

    @dp.message(Command("catalog"))
    async def cmd_catalog(message: Message):
        """Показать каталог категорий"""
        try:
            from app.services.catalog import get_categories
            from app.keyboards.user import categories_keyboard

            categories = await get_categories()

            if not categories:
                await message.answer(
                    "📁 Категории товаров еще не добавлены.\n"
                    "Администратор может добавить их через /admin"
                )
                return

            await message.answer(
                "🐶 <b>Barkery Shop</b>\n\nВыберите категорию:",
                parse_mode="HTML",
                reply_markup=categories_keyboard(categories)
            )
        except Exception as e:
            logger.error(f"Ошибка каталога: {e}")
            await message.answer("📁 Каталог товаров")

    @dp.message(Command("cart"))
    async def cmd_cart(message: Message):
        """Показать корзину"""
        try:
            from app.services.cart import get_cart_total
            from app.keyboards.user import cart_keyboard

            result = await get_cart_total(message.from_user.id)

            if not result.get('success', False):
                if 'unavailable_items' in result:
                    text = "🔄 *Корзина обновлена*\n\n"
                    text += "Некоторые товары стали недоступны:\n"

                    for item in result['unavailable_items']:
                        if item['available'] > 0:
                            text += f"• {item['name']}: доступно {item['available']}г (было {item['requested']}г)\n"
                        else:
                            text += f"• {item['name']}: товар закончился\n"

                    text += "\nКорзина автоматически обновлена."
                    await message.answer(text, parse_mode="Markdown")

                    result = await get_cart_total(message.from_user.id)
                else:
                    await message.answer("🛒 Корзина пуста")
                    return

            items = result.get('items', [])
            total = result.get('total', 0)

            if not items:
                await message.answer("🛒 Корзина пуста")
                return

            text = "🛒 *Ваша корзина:*\n\n"

            for item in items:
                if item.product:
                    subtotal = item.product.price * item.quantity / 100
                    text += f"• *{item.product.name}*\n"
                    text += f"  {item.quantity}г × {item.product.price} RSD/100г = {int(subtotal)} RSD\n\n"

            text += f"*Итого:* {int(total)} RSD"

            await message.answer(text, parse_mode="Markdown", reply_markup=cart_keyboard())

        except Exception as e:
            logger.error(f"Ошибка корзины: {e}")
            await message.answer("🛒 Корзина")

    @dp.message(Command("admin"))
    async def cmd_admin(message: Message):
        """Обработчик /admin"""
        if message.from_user.id != admin_id:
            await message.answer("❌ У вас нет доступа к админ-панели")
            return

        from app.keyboards.admin import admin_menu
        await message.answer("⚙️ Админ-панель Barkery", reply_markup=admin_menu())

    @dp.message(Command("stock"))
    async def cmd_stock(message: Message):
        """Управление остатками"""
        if message.from_user.id != admin_id:
            await message.answer("❌ У вас нет доступа к этой команде")
            return

        try:
            from app.services.stock import stock_service

            # Получаем товары с низкими остатками
            low_stock = await stock_service.get_low_stock_products(threshold=1000)
            out_of_stock = await stock_service.get_out_of_stock_products()

            text = "📊 <b>Управление остатками</b>\n\n"

            if low_stock:
                text += f"⚠️ <b>Низкие остатки (менее 1000г):</b> {len(low_stock)}\n"
                for product in low_stock[:5]:
                    text += f"• {product.name}: {product.stock_grams}г\n"
                if len(low_stock) > 5:
                    text += f"... и еще {len(low_stock) - 5} товаров\n"
                text += "\n"

            if out_of_stock:
                text += f"❌ <b>Нет в наличии:</b> {len(out_of_stock)}\n"
                for product in out_of_stock[:5]:
                    text += f"• {product.name}\n"
                if len(out_of_stock) > 5:
                    text += f"... и еще {len(out_of_stock) - 5} товаров\n"

            if not low_stock and not out_of_stock:
                text += "✅ Все товары в наличии с достаточными остатками!"

            await message.answer(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка команды /stock: {e}")
            await message.answer("❌ Ошибка при получении информации об остатках")

    @dp.message(Command("orders"))
    async def cmd_orders(message: Message):
        """Просмотр заказов"""
        if message.from_user.id != admin_id:
            await message.answer("❌ У вас нет доступа к этой команде")
            return

        try:
            from app.services.orders import order_service

            stats = await order_service.get_order_stats(days=7)

            text = "🛒 <b>Статистика заказов</b>\n\n"
            text += f"<b>За последние 7 дней:</b>\n"
            text += f"• Заказов: {stats['recent']['orders']}\n"
            text += f"• На сумму: {int(stats['recent']['revenue'])} RSD\n\n"

            text += f"<b>Всего за все время:</b>\n"
            text += f"• Заказов: {stats['total']['orders']}\n"
            text += f"• Общая выручка: {int(stats['total']['revenue'])} RSD\n\n"

            text += "<b>По статусам:</b>\n"
            for status, count in stats['by_status'].items():
                status_name = {
                    'pending': '⏳ Ожидают',
                    'confirmed': '✅ Подтверждены',
                    'completed': '🎉 Завершены',
                    'cancelled': '❌ Отменены'
                }.get(status, status)
                text += f"{status_name}: {count}\n"

            await message.answer(text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка команды /orders: {e}")
            await message.answer("❌ Ошибка при получении статистики заказов")

    @dp.message(Command("backup"))
    async def cmd_backup(message: Message):
        """Ручное создание резервной копии"""
        if message.from_user.id != admin_id:
            await message.answer("❌ У вас нет доступа к этой команде")
            return

        try:
            from app.db.backup import backup_database

            await message.answer("🔄 Создание резервной копии...")
            result = await backup_database()

            if result['success']:
                await message.answer(
                    f"✅ Резервная копия создана успешно!\n"
                    f"Время: {result['timestamp']}\n"
                    f"Файл: {result['path']}"
                )
            else:
                await message.answer(
                    f"❌ Ошибка при создании резервной копии:\n"
                    f"{result.get('error', 'Неизвестная ошибка')}"
                )

        except Exception as e:
            logger.error(f"Ошибка команды /backup: {e}")
            await message.answer("❌ Ошибка при создании резервной копии")

    @dp.message(Command("add_product"))
    async def cmd_add_product(message: Message):
        """Добавление товара"""
        if message.from_user.id != admin_id:
            await message.answer("❌ У вас нет доступа к этой команде")
            return

        await message.answer(
            "➕ <b>Добавление товара</b>\n\n"
            "Используйте формат:\n"
            "<code>/add_product Название | Описание | Цена | ID_категории | Количество_грамм</code>\n\n"
            "Пример:\n"
            "<code>/add_product Сушеная курица | Натуральная сушеная курица | 300 | 1 | 5000</code>",
            parse_mode="HTML"
        )

    @dp.message(Command("add_category"))
    async def cmd_add_category(message: Message):
        """Добавление категории"""
        if message.from_user.id != admin_id:
            await message.answer("❌ У вас нет доступа к этой команде")
            return

        await message.answer(
            "📂 <b>Добавление категории</b>\n\n"
            "Используйте формат:\n"
            "<code>/add_category Название_категории</code>\n\n"
            "Пример:\n"
            "<code>/add_category Новые лакомства</code>",
            parse_mode="HTML"
        )

    # ========== CALLBACK HANDLERS ==========
    @dp.callback_query(F.data.startswith("category:"))
    async def handle_category(callback: CallbackQuery):
        """Показать товары в категории"""
        try:
            from app.services.catalog import get_products_by_category
            from app.keyboards.user import products_keyboard

            category = callback.data.split(":")[1]
            products = await get_products_by_category(category)

            if not products:
                await callback.message.edit_text(
                    f"📦 {category}\n\n"
                    f"В этой категории пока нет товаров.",
                    reply_markup=products_keyboard([], category)
                )
                return

            text = f"📦 {category}\n\n"
            unavailable_count = sum(1 for p in products if not (p.available and p.stock_grams > 0))

            if unavailable_count:
                text += f"⚠️ {unavailable_count} товаров временно недоступно\n\n"

            await callback.message.edit_text(
                text,
                reply_markup=products_keyboard(products, category, show_unavailable=True)
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка категории: {e}")
            await callback.answer("❌ Ошибка загрузки категории", show_alert=True)

    @dp.callback_query(F.data.startswith("product:"))
    async def handle_product(callback: CallbackQuery):
        """Показать товар"""
        try:
            parts = callback.data.split(":")
            if len(parts) < 3:
                await callback.answer("❌ Ошибка формата")
                return

            if parts[1] == "unavailable":
                product_id = int(parts[2])
                from app.services.catalog import get_product
                product = await get_product(product_id)

                if product:
                    text = f"❌ <b>{product.name}</b>\n\n"
                    if not product.available:
                        text += "Товар временно недоступен.\n"
                    elif product.stock_grams <= 0:
                        text += "Товар закончился.\n"
                    text += f"💰 Цена: <b>{product.price} RSD/100г</b>\n"
                    if product.description:
                        text += f"\n{product.description}"

                    await callback.message.answer(text, parse_mode="HTML")
                await callback.answer()
                return

            product_id = int(parts[1])
            category = parts[2]

            from app.services.catalog import get_product
            from app.keyboards.user import quantity_keyboard

            product = await get_product(product_id)

            if not product:
                await callback.answer("❌ Товар не найден", show_alert=True)
                return

            if not product.available or product.stock_grams <= 0:
                await callback.answer("❌ Товар временно недоступен", show_alert=True)
                return

            await callback.message.edit_text(
                f"<b>{product.name}</b>\n\n"
                f"{product.description or ''}\n\n"
                f"💰 Цена: <b>{product.price} RSD/100г</b>\n"
                f"📦 В наличии: <b>{product.stock_grams}г</b>",
                parse_mode="HTML",
                reply_markup=quantity_keyboard(product.id, category, product.price)
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка товара: {e}")
            await callback.answer("❌ Ошибка загрузки товара", show_alert=True)

    @dp.callback_query(F.data.startswith("qty:"))
    async def handle_quantity(callback: CallbackQuery):
        """Изменение количества товара"""
        try:
            parts = callback.data.split(":")
            if len(parts) != 5:
                await callback.answer("❌ Ошибка")
                return

            _, product_id_str, action, category, current_qty_str = parts

            product_id = int(product_id_str)
            current_qty = int(current_qty_str)

            if action == "inc":
                new_qty = current_qty + 100
            elif action == "dec":
                new_qty = max(100, current_qty - 100)
            else:
                await callback.answer("❌ Неизвестное действие")
                return

            if new_qty == current_qty:
                await callback.answer(f"Минимальное количество: 100г")
                return

            from app.services.catalog import get_product
            from app.keyboards.user import quantity_keyboard

            product = await get_product(product_id)
            if not product:
                await callback.answer("❌ Товар не найден")
                return

            new_keyboard = quantity_keyboard(
                product_id=product_id,
                category=category,
                price=product.price,
                qty=new_qty
            )

            await callback.message.edit_reply_markup(reply_markup=new_keyboard)
            await callback.answer(f"Количество: {new_qty}г")

        except Exception as e:
            logger.error(f"Ошибка количества: {e}")
            await callback.answer("❌ Ошибка обновления")

    @dp.callback_query(F.data.startswith("cart:add:"))
    async def handle_cart_add(callback: CallbackQuery):
        """Добавление товара в корзину"""
        try:
            parts = callback.data.split(":")
            if len(parts) != 5:
                await callback.answer("❌ Ошибка формата", show_alert=True)
                return

            product_id = int(parts[2])
            quantity = int(parts[3])

            from app.services.cart import add_to_cart
            result = await add_to_cart(
                user_id=callback.from_user.id,
                product_id=product_id,
                quantity=quantity
            )

            if result['success']:
                await callback.answer(f"✅ Добавлено {quantity}г")
            else:
                error_msg = result.get('error', 'Неизвестная ошибка')
                if 'available_qty' in result and result['available_qty'] > 0:
                    await callback.answer(
                        f"⚠️ {error_msg}. Добавить {result['available_qty']}г?",
                        show_alert=True
                    )
                else:
                    await callback.answer(f"❌ {error_msg}", show_alert=True)

        except Exception as e:
            logger.error(f"Ошибка добавления в корзину: {e}")
            await callback.answer("❌ Ошибка добавления", show_alert=True)

    @dp.callback_query(F.data == "cart:clear")
    async def handle_cart_clear(callback: CallbackQuery):
        """Очистка корзины"""
        try:
            from app.services.cart import clear_cart
            result = await clear_cart(callback.from_user.id)

            if result['success']:
                await callback.message.edit_text("🗑 Корзина очищена")
            else:
                await callback.answer("❌ Ошибка при очистке корзины", show_alert=True)

            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка очистки корзины: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)

    @dp.callback_query(F.data == "show_cart")
    async def handle_show_cart(callback: CallbackQuery):
        """Показать корзину из callback"""
        await cmd_cart(callback.message)
        await callback.answer()

    @dp.callback_query(F.data == "back_to_categories")
    async def handle_back_to_categories(callback: CallbackQuery):
        """Вернуться к категориям"""
        try:
            from app.services.catalog import get_categories
            from app.keyboards.user import categories_keyboard

            categories = await get_categories()

            await callback.message.edit_text(
                "🐶 <b>Barkery Shop</b>\n\nВыберите категориу:",  # Опечатка в исходнике: "категориу"
                parse_mode="HTML",
                reply_markup=categories_keyboard(categories)
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка возврата к категориям: {e}")
            await callback.answer("❌ Ошибка", show_alert=True)

    # ========== АДМИН CALLBACK HANDLERS ==========
    @dp.callback_query(F.data == "admin:back")
    async def admin_back(callback: CallbackQuery):
        """Вернуться в админ-меню"""
        if callback.from_user.id != admin_id:
            await callback.answer("❌ Нет доступа")
            return

        from app.keyboards.admin import admin_menu
        await callback.message.edit_text("⚙️ Админ-панель Barkery", reply_markup=admin_menu())
        await callback.answer()

    @dp.callback_query(F.data == "admin:products")
    async def admin_products(callback: CallbackQuery):
        """Управление товарами"""
        if callback.from_user.id != admin_id:
            await callback.answer("❌ Нет доступа")
            return

        await callback.message.answer(
            "📦 <b>Управление товарами</b>\n\nИспользуйте команды:\n/add_product - добавить товар\n/add_category - добавить категориу",  # Опечатка в исходнике: "категориу"
            parse_mode="HTML")
        await callback.answer()

    @dp.callback_query(F.data == "admin:stock")
    async def admin_stock(callback: CallbackQuery):
        """Управление остатками"""
        if callback.from_user.id != admin_id:
            await callback.answer("❌ Нет доступа")
            return

        await cmd_stock(callback.message)
        await callback.answer()

    @dp.callback_query(F.data == "admin:orders")
    async def admin_orders(callback: CallbackQuery):
        """Управление заказами"""
        if callback.from_user.id != admin_id:
            await callback.answer("❌ Нет доступа")
            return

        await cmd_orders(callback.message)
        await callback.answer()

    @dp.callback_query(F.data == "admin:add_product")
    async def admin_add_product(callback: CallbackQuery):
        """Добавить товар"""
        if callback.from_user.id != admin_id:
            await callback.answer("❌ Нет доступа")
            return

        await cmd_add_product(callback.message)
        await callback.answer()

    @dp.callback_query(F.data == "admin_add_category")
    async def admin_add_category(callback: CallbackQuery):
        """Добавить категорию"""
        if callback.from_user.id != admin_id:
            await callback.answer("❌ Нет доступа")
            return

        await cmd_add_category(callback.message)
        await callback.answer()

    @dp.callback_query(F.data == "close")
    async def close_menu(callback: CallbackQuery):
        """Закрыть меню"""
        try:
            await callback.message.delete()
            await callback.answer("Меню закрыто")
        except Exception as e:
            await callback.answer("❌ Ошибка", show_alert=True)

    # 3. Проверяем хендлеры
    message_handlers = list(dp.message.handlers)
    callback_handlers = list(dp.callback_query.handlers)

    logger.info(f"📊 Хендлеров: {len(message_handlers)} сообщений, {len(callback_handlers)} callback")

    if len(message_handlers) == 0:
        logger.error("❌ Нет хендлеров!")
        return

    # 4. Инициализируем базу данных с тестовыми данными
    try:
        from app.db.engine import engine
        from app.db.models import Base
        from app.db.session import get_session
        from app.db.models import Category, Product

        # Создаем таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База данных инициализирована")

        # Добавляем тестовые данные если их нет
        async for session in get_session():
            # Проверяем категории
            result = await session.execute(text("SELECT COUNT(*) FROM categories"))
            count = result.scalar()

            if count == 0:
                categories = [
                    Category(name="Сухие лакомства"),
                    Category(name="Консервы"),
                    Category(name="Кости и игрушки")
                ]
                session.add_all(categories)
                await session.commit()
                logger.info("✅ Добавлены тестовые категории")

                # Перезагружаем сессию для получения ID категорий
                await session.flush()

                # Получаем ID категорий для добавления товаров
                result = await session.execute(text("SELECT id, name FROM categories"))
                category_data = result.all()

                if category_data:
                    category_map = {name: id for id, name in category_data}

                    # Добавляем тестовые товары
                    test_products = [
                        Product(
                            name="Сушеная говядина",
                            description="100% натуральная сушеная говядина для собак",
                            price=350.0,
                            category_id=category_map.get("Сухие лакомства"),
                            stock_grams=5000,
                            available=True
                        ),
                        Product(
                            name="Куриные сердечки",
                            description="Сушеные куриные сердечки, богатые белком",
                            price=280.0,
                            category_id=category_map.get("Сухие лакомства"),
                            stock_grams=3000,
                            available=True
                        ),
                        Product(
                            name="Консерва с телятиной",
                            description="Консервированное мясо телятины для собак",
                            price=450.0,
                            category_id=category_map.get("Консервы"),
                            stock_grams=0,
                            available=False
                        ),
                        Product(
                            name="Жевательная кость",
                            description="Натуральная жевательная кость для чистки зубов",
                            price=200.0,
                            category_id=category_map.get("Кости и игрушки"),
                            stock_grams=1000,
                            available=True
                        ),
                    ]

                    # Фильтруем товары с существующими категориями
                    valid_products = [p for p in test_products if p.category_id is not None]
                    session.add_all(valid_products)
                    await session.commit()
                    logger.info(f"✅ Добавлено {len(valid_products)} тестовых товаров")

    except Exception as e:
        logger.warning(f"⚠️ База данных: {e}")

    # 5. Запускаем планировщик резервного копирования
    try:
        from app.scheduler import setup_backup_schedule, start_scheduler
        setup_backup_schedule()
        start_scheduler()
        logger.info("✅ Планировщик резервного копирования запущен")
    except Exception as e:
        logger.warning(f"⚠️ Планировщик: {e}")

    # 6. Запускаем бота
    logger.info("\n" + "=" * 50)
    logger.info("🚀 БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    logger.info(f"🤖 Admin ID: {admin_id}")
    logger.info("📱 Основные команды:")
    logger.info("   /start - главное меню")
    logger.info("   /catalog - каталог товаров")
    logger.info("   /cart - корзина")
    logger.info("   /help - помощь")
    logger.info("   /admin - админ-панель (только для админа)")
    logger.info("   /stock - остатки товаров")
    logger.info("   /orders - статистика заказов")
    logger.info("   /backup - ручное резервное копирование")
    logger.info("=" * 50)

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("\n⏹ Остановка по запросу пользователя")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())