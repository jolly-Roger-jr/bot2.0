# app/handlers/admin/stock.py - ПОЛНОСТЬЮ ПЕРЕРАБОТАННЫЙ

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import settings
from app.services.catalog import get_categories, get_products_by_category, get_product
from app.services.stock import stock_service
from app.keyboards.admin import back_to_admin_menu

router = Router()


class StockManagement(StatesGroup):
    """Состояния для управления остатками"""
    waiting_product_selection = State()
    waiting_stock_update = State()
    waiting_availability_toggle = State()


@router.message(Command("stock"))
async def stock_management_menu(message: Message):
    """Главное меню управления остатками"""
    if message.from_user.id != settings.admin_id:
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Просмотреть остатки", callback_data="stock:view")],
            [InlineKeyboardButton(text="➕ Добавить остатки", callback_data="stock:add")],
            [InlineKeyboardButton(text="📝 Изменить остатки", callback_data="stock:edit")],
            [InlineKeyboardButton(text="⚠️ Низкие остатки", callback_data="stock:low")],
            [InlineKeyboardButton(text="❌ Нет в наличии", callback_data="stock:out")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back")]
        ]
    )

    await message.answer(
        "📦 <b>Управление остатками товаров</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "stock:view")
async def view_stock_menu(callback: CallbackQuery):
    """Меню просмотра остатков по категориям"""
    categories = await get_categories()

    if not categories:
        await callback.message.edit_text(
            "❌ Категории товаров не найдены",
            reply_markup=back_to_admin_menu()
        )
        return

    # Создаем кнопки для каждой категории
    buttons = []
    for category in categories:
        buttons.append([
            InlineKeyboardButton(
                text=f"📂 {category}",
                callback_data=f"stock:view_category:{category}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stock:back")])

    await callback.message.edit_text(
        "📂 <b>Выберите категорию для просмотра остатков:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stock:view_category:"))
async def view_category_stock(callback: CallbackQuery):
    """Показать остатки товаров в выбранной категории"""
    category_name = callback.data.split(":")[2]
    products = await get_products_by_category(category_name)

    if not products:
        await callback.message.edit_text(
            f"❌ В категории '{category_name}' нет товаров",
            reply_markup=back_to_admin_menu()
        )
        return

    text = f"📦 <b>Остатки товаров: {category_name}</b>\n\n"

    for product in products:
        # Получаем актуальные данные об остатках
        stock_info = await stock_service.get_product_stock(product.id)
        if stock_info:
            status = "✅" if stock_info['available'] else "❌"
            stock_status = f"{stock_info['stock_grams']}г" if stock_info['stock_grams'] > 0 else "Нет в наличии"
            text += f"{status} <b>{product.name}</b>\n"
            text += f"   Остатки: {stock_status}\n"
            text += f"   Цена: {product.price} RSD/100г\n"
            text += f"   ID: {product.id}\n\n"

    # Кнопки управления для каждого товара
    buttons = []
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {product.name[:20]}...",
                callback_data=f"stock:edit_product:{product.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад к категориям", callback_data="stock:view")])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stock:edit_product:"))
async def edit_product_stock(callback: CallbackQuery):
    """Меню редактирования остатков конкретного товара"""
    product_id = int(callback.data.split(":")[2])
    product = await get_product(product_id)

    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    stock_info = await stock_service.get_product_stock(product_id)

    text = f"✏️ <b>Управление товаром:</b>\n\n"
    text += f"<b>Название:</b> {product.name}\n"
    text += f"<b>Категория:</b> {stock_info['category'] if stock_info else 'Неизвестно'}\n"
    text += f"<b>Цена:</b> {product.price} RSD/100г\n"
    text += f"<b>Статус:</b> {'✅ В наличии' if stock_info and stock_info['available'] else '❌ Нет в наличии'}\n"
    text += f"<b>Остатки:</b> {stock_info['stock_grams'] if stock_info else 0} грамм\n\n"
    text += "<b>Выберите действие:</b>"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Добавить", callback_data=f"stock:add_grams:{product_id}"),
                InlineKeyboardButton(text="➖ Уменьшить", callback_data=f"stock:sub_grams:{product_id}")
            ],
            [
                InlineKeyboardButton(
                    text="✅ Включить" if not stock_info['available'] else "❌ Выключить",
                    callback_data=f"stock:toggle:{product_id}"
                )
            ],
            [
                InlineKeyboardButton(text="📝 Установить точно", callback_data=f"stock:set_exact:{product_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data=f"stock:view_category:{stock_info['category']}")
            ]
        ]
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("stock:add_grams:"))
async def add_stock_dialog(callback: CallbackQuery, state: FSMContext):
    """Диалог добавления остатков"""
    product_id = int(callback.data.split(":")[2])

    await state.set_state(StockManagement.waiting_stock_update)
    await state.update_data(
        action="add",
        product_id=product_id
    )

    await callback.message.edit_text(
        "➕ <b>Добавление остатков</b>\n\n"
        "Введите количество грамм для добавления:\n"
        "<i>Например: 500 (добавит 500 грамм к текущим остаткам)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отмена", callback_data=f"stock:edit_product:{product_id}")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stock:sub_grams:"))
async def subtract_stock_dialog(callback: CallbackQuery, state: FSMContext):
    """Диалог уменьшения остатков"""
    product_id = int(callback.data.split(":")[2])

    await state.set_state(StockManagement.waiting_stock_update)
    await state.update_data(
        action="subtract",
        product_id=product_id
    )

    await callback.message.edit_text(
        "➖ <b>Уменьшение остатков</b>\n\n"
        "Введите количество грамм для уменьшения:\n"
        "<i>Например: 200 (уменьшит остатки на 200 грамм)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отмена", callback_data=f"stock:edit_product:{product_id}")]
            ]
        )
    )
    await callback.answer()


@router.callback_query(F.data.startswith("stock:set_exact:"))
async def set_exact_stock_dialog(callback: CallbackQuery, state: FSMContext):
    """Диалог установки точного количества остатков"""
    product_id = int(callback.data.split(":")[2])

    await state.set_state(StockManagement.waiting_stock_update)
    await state.update_data(
        action="set_exact",
        product_id=product_id
    )

    await callback.message.edit_text(
        "📝 <b>Установка точного количества остатков</b>\n\n"
        "Введите новое количество грамм:\n"
        "<i>Например: 1500 (установит остатки ровно в 1500 грамм)</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отмена", callback_data=f"stock:edit_product:{product_id}")]
            ]
        )
    )
    await callback.answer()


@router.message(StockManagement.waiting_stock_update)
async def process_stock_update(message: Message, state: FSMContext):
    """Обработка ввода количества грамм для обновления остатков"""
    data = await state.get_data()
    product_id = data.get('product_id')
    action = data.get('action')

    try:
        grams = int(message.text.strip())
        if grams <= 0:
            await message.answer("❌ Количество должно быть положительным числом. Попробуйте еще раз:")
            return

        product = await get_product(product_id)
        if not product:
            await message.answer("❌ Товар не найден")
            await state.clear()
            return

        # Выполняем действие в зависимости от типа
        if action == "add":
            success = await stock_service.add_stock(product_id, grams)
            action_text = "добавлено"
        elif action == "subtract":
            success = await stock_service.subtract_stock(product_id, grams)
            action_text = "уменьшено"
        elif action == "set_exact":
            # Для установки точного значения используем update_stock
            current_info = await stock_service.get_product_stock(product_id)
            if current_info:
                success = await stock_service.update_stock(product_id, grams, current_info['available'])
                action_text = "установлено"
            else:
                success = False
        else:
            success = False

        if success:
            # Получаем обновленную информацию
            updated_info = await stock_service.get_product_stock(product_id)

            await message.answer(
                f"✅ <b>Остатки обновлены!</b>\n\n"
                f"<b>Товар:</b> {product.name}\n"
                f"<b>Действие:</b> {action_text} {grams} грамм\n"
                f"<b>Новые остатки:</b> {updated_info['stock_grams']} грамм\n"
                f"<b>Статус:</b> {'✅ В наличии' if updated_info['available'] else '❌ Нет в наличии'}",
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Ошибка при обновлении остатков")

        # Возвращаем к меню товара
        from app.handlers.admin.stock import edit_product_stock
        # Нужно отправить callback, но мы в message handler
        # Вместо этого отправляем команду для возврата
        await message.answer(
            "Вы можете продолжить управление остатками через меню /stock",
            reply_markup=back_to_admin_menu()
        )

    except ValueError:
        await message.answer("❌ Пожалуйста, введите число. Попробуйте еще раз:")
        return

    await state.clear()


@router.callback_query(F.data.startswith("stock:toggle:"))
async def toggle_availability(callback: CallbackQuery):
    """Переключение доступности товара"""
    product_id = int(callback.data.split(":")[2])

    product = await get_product(product_id)
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return

    # Получаем текущий статус
    stock_info = await stock_service.get_product_stock(product_id)
    if not stock_info:
        await callback.answer("❌ Ошибка получения данных", show_alert=True)
        return

    # Переключаем статус
    new_status = not stock_info['available']
    success = await stock_service.set_availability(product_id, new_status)

    if success:
        status_text = "включен" if new_status else "выключен"
        await callback.answer(f"✅ Товар {status_text}", show_alert=True)

        # Обновляем сообщение
        await edit_product_stock(callback)
    else:
        await callback.answer("❌ Ошибка при изменении статуса", show_alert=True)


@router.callback_query(F.data == "stock:low")
async def show_low_stock(callback: CallbackQuery):
    """Показать товары с низкими остатками"""
    low_stock_products = await stock_service.get_low_stock_products(threshold=1000)

    if not low_stock_products:
        await callback.message.edit_text(
            "✅ <b>Все товары имеют достаточные остатки</b>\n"
            "(более 1000 грамм)",
            parse_mode="HTML",
            reply_markup=back_to_admin_menu()
        )
        return

    text = "⚠️ <b>Товары с низкими остатками (менее 1000г):</b>\n\n"

    for product in low_stock_products:
        text += f"• <b>{product.name}</b>\n"
        text += f"  Остатки: {product.stock_grams} грамм\n"
        text += f"  Категория: {product.category.name if product.category else 'Неизвестно'}\n"
        text += f"  ID: {product.id}\n\n"

    text += "\n<i>Рекомендуется пополнить остатки</i>"

    # Кнопки для быстрого управления
    buttons = []
    for product in low_stock_products[:5]:  # Показываем первые 5
        buttons.append([
            InlineKeyboardButton(
                text=f"➕ Пополнить {product.name[:15]}...",
                callback_data=f"stock:add_grams:{product.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stock:back")])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "stock:out")
async def show_out_of_stock(callback: CallbackQuery):
    """Показать товары без остатков"""
    out_of_stock_products = await stock_service.get_out_of_stock_products()

    if not out_of_stock_products:
        await callback.message.edit_text(
            "✅ <b>Все товары есть в наличии</b>",
            parse_mode="HTML",
            reply_markup=back_to_admin_menu()
        )
        return

    text = "❌ <b>Товары без остатков:</b>\n\n"

    for product in out_of_stock_products:
        status = "❌" if not product.available else "⚠️"
        text += f"{status} <b>{product.name}</b>\n"
        text += f"  Категория: {product.category.name if product.category else 'Неизвестно'}\n"
        text += f"  ID: {product.id}\n\n"

    # Кнопки для управления
    buttons = []
    for product in out_of_stock_products[:5]:
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {product.name[:15]}...",
                callback_data=f"stock:edit_product:{product.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="stock:back")])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data == "stock:back")
async def back_to_stock_menu(callback: CallbackQuery):
    """Вернуться в меню управления остатками"""
    await stock_management_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data == "admin:back")
async def back_to_admin_panel(callback: CallbackQuery):
    """Вернуться в админ-панель"""
    from app.handlers.admin.panel import admin_entry
    await admin_entry(callback.message)
    await callback.answer()