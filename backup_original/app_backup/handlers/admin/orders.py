# app/handlers/admin/orders.py - НОВЫЙ ФАЙЛ

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import settings
from app.services.orders import order_service
from app.services.user_notifications import user_notification_service
from app.keyboards.admin import back_to_admin_menu
from app.db.session import get_session
from app.db.models import Order, OrderItem

router = Router()


class OrderSearch(StatesGroup):
    """Состояния для поиска заказов"""
    waiting_search_term = State()


@router.message(Command("orders"))
async def orders_management_menu(message: Message):
    """Главное меню управления заказами"""
    if message.from_user.id != settings.admin_id:
        return

    # Получаем статистику
    stats = await order_service.get_order_stats(days=7)

    text = "📋 <b>Управление заказами</b>\n\n"
    text += f"<b>Статистика за 7 дней:</b>\n"
    text += f"• Заказов: {stats['recent']['orders']}\n"
    text += f"• На сумму: {int(stats['recent']['revenue'])} RSD\n\n"

    text += f"<b>Всего заказов:</b> {stats['total']['orders']}\n"
    text += f"<b>Общая выручка:</b> {int(stats['total']['revenue'])} RSD\n\n"

    text += "<b>По статусам:</b>\n"
    for status, count in stats['by_status'].items():
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'processing': '🚚',
            'completed': '🎉',
            'cancelled': '❌'
        }.get(status, '📦')

        status_name = {
            'pending': 'Ожидают',
            'confirmed': 'Подтверждены',
            'processing': 'В работе',
            'completed': 'Завершены',
            'cancelled': 'Отменены'
        }.get(status, status)

        text += f"{status_emoji} {status_name}: {count}\n"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Ожидают", callback_data="admin:orders:pending"),
                InlineKeyboardButton(text="✅ Подтверждены", callback_data="admin:orders:confirmed")
            ],
            [
                InlineKeyboardButton(text="🚚 В работе", callback_data="admin:orders:processing"),
                InlineKeyboardButton(text="🎉 Завершены", callback_data="admin:orders:completed")
            ],
            [
                InlineKeyboardButton(text="❌ Отменены", callback_data="admin:orders:cancelled"),
                InlineKeyboardButton(text="📋 Сегодня", callback_data="admin:orders:today")
            ],
            [
                InlineKeyboardButton(text="🔍 Поиск заказа", callback_data="admin:order:search"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin:orders:stats")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back")
            ]
        ]
    )

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data.startswith("admin:orders:"))
async def show_orders_by_status(callback: CallbackQuery):
    """Показать заказы по статусу"""
    status = callback.data.split(":")[2]

    if status == "today":
        orders = await order_service.get_todays_orders()
        title = "📅 Сегодняшние заказы"
    else:
        orders = await order_service.get_all_orders(status=status, limit=30)
        status_names = {
            'pending': '⏳ Ожидают подтверждения',
            'confirmed': '✅ Подтвержденные',
            'processing': '🚚 В работе',
            'completed': '🎉 Завершенные',
            'cancelled': '❌ Отмененные'
        }
        title = status_names.get(status, status)

    if not orders:
        await callback.message.edit_text(
            f"{title}\n\nНет заказов.",
            reply_markup=back_to_admin_menu()
        )
        await callback.answer()
        return

    text = f"{title}\n\n"

    # Показываем список заказов
    for i, order in enumerate(orders[:15], 1):  # Ограничиваем 15 заказами
        created = order.created_at.strftime("%d.%m %H:%M")
        text += f"{i}. <b>#{order.id}</b> - {created}\n"
        text += f"   {order.customer_name or 'Без имени'} - {int(order.total_amount)} RSD\n"
        text += f"   📞 {order.phone or 'Нет телефона'}\n\n"

    if len(orders) > 15:
        text += f"\n... и еще {len(orders) - 15} заказов"

    # Кнопки для каждого заказа
    buttons = []
    for order in orders[:10]:  # Кнопки для первых 10 заказов
        btn_text = f"#{order.id} - {int(order.total_amount)} RSD"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"admin:order:view:{order.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin:orders:menu")])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:view:"))
async def view_order_details(callback: CallbackQuery, bot: Bot):
    """Просмотр деталей заказа"""
    order_id = int(callback.data.split(":")[3])

    order = await order_service.get_order(order_id)

    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    # Формируем детальную информацию
    text = f"📋 <b>Заказ #{order.id}</b>\n\n"

    # Информация о заказе
    created = order.created_at.strftime("%d.%m.%Y %H:%M")
    text += f"<b>Дата:</b> {created}\n"

    status_emoji = {
        'pending': '⏳',
        'confirmed': '✅',
        'processing': '🚚',
        'completed': '🎉',
        'cancelled': '❌'
    }.get(order.status, '📦')

    status_name = {
        'pending': 'Ожидает подтверждения',
        'confirmed': 'Подтвержден',
        'processing': 'В работе',
        'completed': 'Завершен',
        'cancelled': 'Отменен'
    }.get(order.status, order.status)

    text += f"<b>Статус:</b> {status_emoji} {status_name}\n\n"

    # Информация о покупателе
    text += f"<b>👤 Покупатель:</b>\n"
    text += f"• ID: {order.user_id}\n"
    if order.customer_name:
        text += f"• Имя: {order.customer_name}\n"
    if order.phone:
        text += f"• Телефон: {order.phone}\n"

    # Адрес
    text += f"\n<b>📍 Адрес доставки:</b>\n{order.address}\n\n"

    # Товары
    text += f"<b>📦 Товары ({len(order.items)}):</b>\n"
    for item in order.items:
        item_total = item.price_per_100g * item.quantity / 100
        product_name = item.product_name or (item.product.name if item.product else "Неизвестный товар")
        text += f"• {product_name}\n"
        text += f"  {item.quantity}г × {item.price_per_100g} RSD/100г = {int(item_total)} RSD\n"

    text += f"\n<b>💰 Итого:</b> {int(order.total_amount)} RSD"

    # Клавиатура управления
    keyboard_buttons = []

    # Кнопки изменения статуса
    if order.status == 'pending':
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"admin:order:confirm:{order.id}"
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"admin:order:cancel:{order.id}"
            )
        ])
    elif order.status == 'confirmed':
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="🚚 В работу",
                callback_data=f"admin:order:processing:{order.id}"
            )
        ])
    elif order.status == 'processing':
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="🎉 Завершить",
                callback_data=f"admin:order:complete:{order.id}"
            )
        ])

    # Кнопки связи
    contact_buttons = []
    if order.phone:
        contact_buttons.append(
            InlineKeyboardButton(
                text="📞 Позвонить",
                url=f"tel:{order.phone}"
            )
        )

    contact_buttons.append(
        InlineKeyboardButton(
            text="💬 Написать в Telegram",
            url=f"tg://user?id={order.user_id}"
        )
    )

    if contact_buttons:
        keyboard_buttons.append(contact_buttons)

    # Кнопки навигации
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin:orders:menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:order:confirm:"))
async def confirm_order(callback: CallbackQuery, bot: Bot):
    """Подтвердить заказ"""
    order_id = int(callback.data.split(":")[3])

    # Получаем текущий статус
    order = await order_service.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    old_status = order.status

    # Меняем статус
    success = await order_service.update_order_status(order_id, 'confirmed')

    if success:
        # Уведомляем пользователя
        await user_notification_service.notify_order_status_change(
            bot=bot,
            user_id=order.user_id,
            order_id=order_id,
            old_status=old_status,
            new_status='confirmed'
        )

        await callback.answer("✅ Заказ подтвержден", show_alert=True)

        # Обновляем сообщение
        await view_order_details(callback, bot)
    else:
        await callback.answer("❌ Ошибка при подтверждении", show_alert=True)


@router.callback_query(F.data.startswith("admin:order:cancel:"))
async def cancel_order(callback: CallbackQuery, bot: Bot):
    """Отменить заказ"""
    order_id = int(callback.data.split(":")[3])

    order = await order_service.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    old_status = order.status

    # Меняем статус
    success = await order_service.update_order_status(order_id, 'cancelled')

    if success:
        # Уведомляем пользователя
        await user_notification_service.notify_order_status_change(
            bot=bot,
            user_id=order.user_id,
            order_id=order_id,
            old_status=old_status,
            new_status='cancelled'
        )

        await callback.answer("❌ Заказ отменен", show_alert=True)

        # Обновляем сообщение
        await view_order_details(callback, bot)
    else:
        await callback.answer("❌ Ошибка при отмене", show_alert=True)


@router.callback_query(F.data.startswith("admin:order:processing:"))
async def set_order_processing(callback: CallbackQuery, bot: Bot):
    """Установить статус "В работе" """
    order_id = int(callback.data.split(":")[3])

    order = await order_service.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    old_status = order.status
    success = await order_service.update_order_status(order_id, 'processing')

    if success:
        await user_notification_service.notify_order_status_change(
            bot=bot,
            user_id=order.user_id,
            order_id=order_id,
            old_status=old_status,
            new_status='processing'
        )

        await callback.answer("🚚 Заказ переведен в работу", show_alert=True)
        await view_order_details(callback, bot)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin:order:complete:"))
async def complete_order(callback: CallbackQuery, bot: Bot):
    """Завершить заказ"""
    order_id = int(callback.data.split(":")[3])

    order = await order_service.get_order(order_id)
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    old_status = order.status
    success = await order_service.update_order_status(order_id, 'completed')

    if success:
        await user_notification_service.notify_order_status_change(
            bot=bot,
            user_id=order.user_id,
            order_id=order_id,
            old_status=old_status,
            new_status='completed'
        )

        await callback.answer("🎉 Заказ завершен", show_alert=True)
        await view_order_details(callback, bot)
    else:
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin:order:search")
async def search_order_dialog(callback: CallbackQuery, state: FSMContext):
    """Диалог поиска заказа"""
    await state.set_state(OrderSearch.waiting_search_term)

    await callback.message.edit_text(
        "🔍 <b>Поиск заказа</b>\n\n"
        "Введите:\n"
        "• Номер заказа (например: 42)\n"
        "• Имя покупателя\n"
        "• Номер телефона\n"
        "• ID пользователя\n\n"
        "<i>Или отправьте /cancel для отмены</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin:orders:menu")]
            ]
        )
    )
    await callback.answer()


@router.message(OrderSearch.waiting_search_term)
async def process_order_search(message: Message, state: FSMContext):
    """Обработка поиска заказа"""
    search_term = message.text.strip()

    if search_term.lower() == '/cancel':
        await state.clear()
        await message.answer("❌ Поиск отменен")
        return

    orders = await order_service.search_orders(search_term, limit=20)

    if not orders:
        await message.answer(
            f"🔍 По запросу '<b>{search_term}</b>' ничего не найдено.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    text = f"🔍 <b>Результаты поиска:</b> '{search_term}'\n\n"

    for i, order in enumerate(orders[:10], 1):
        created = order.created_at.strftime("%d.%m %H:%M")
        status_emoji = {
            'pending': '⏳',
            'confirmed': '✅',
            'processing': '🚚',
            'completed': '🎉',
            'cancelled': '❌'
        }.get(order.status, '📦')

        text += f"{i}. {status_emoji} <b>#{order.id}</b> - {created}\n"
        text += f"   {order.customer_name or 'Без имени'} - {int(order.total_amount)} RSD\n"
        text += f"   📞 {order.phone or 'Нет телефона'}\n\n"

    if len(orders) > 10:
        text += f"\n... и еще {len(orders) - 10} заказов"

    # Кнопки для найденных заказов
    buttons = []
    for order in orders[:8]:
        btn_text = f"#{order.id} - {int(order.total_amount)} RSD"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"admin:order:view:{order.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin:orders:menu")])

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

    await state.clear()


@router.callback_query(F.data == "admin:orders:menu")
async def back_to_orders_menu(callback: CallbackQuery):
    """Вернуться в меню заказов"""
    await orders_management_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data == "admin:orders:stats")
async def show_detailed_stats(callback: CallbackQuery):
    """Показать детальную статистику"""
    stats = await order_service.get_order_stats(days=30)

    text = "📊 <b>Детальная статистика</b>\n\n"

    text += f"<b>За 30 дней:</b>\n"
    text += f"• Заказов: {stats['recent']['orders']}\n"
    text += f"• На сумму: {int(stats['recent']['revenue'])} RSD\n"

    if stats['recent']['orders'] > 0:
        avg_recent = stats['recent']['revenue'] / stats['recent']['orders']
        text += f"• Средний чек: {int(avg_recent)} RSD\n"

    text += f"\n<b>Всего за все время:</b>\n"
    text += f"• Заказов: {stats['total']['orders']}\n"
    text += f"• Общая выручка: {int(stats['total']['revenue'])} RSD\n"

    if stats['total']['orders'] > 0:
        text += f"• Средний чек: {int(stats['total']['avg_order'])} RSD\n"

    text += f"\n<b>Распределение по статусам:</b>\n"
    for status, count in stats['by_status'].items():
        percentage = (count / stats['total']['orders'] * 100) if stats['total']['orders'] > 0 else 0

        status_name = {
            'pending': '⏳ Ожидают',
            'confirmed': '✅ Подтверждены',
            'processing': '🚚 В работе',
            'completed': '🎉 Завершены',
            'cancelled': '❌ Отменены'
        }.get(status, status)

        text += f"{status_name}: {count} ({percentage:.1f}%)\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:orders:menu")]
            ]
        )
    )
    await callback.answer()