# app/handlers/admin/panel.py - ДОПОЛНЕННАЯ ВЕРСИЯ

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.config import settings
from app.keyboards.admin import admin_menu, stock_management_menu
from app.db.backup import backup_manager

router = Router()


@router.message(F.text == "/admin")
async def admin_entry(message: Message):
    """Команда /admin - вход в админ-панель"""
    if str(message.from_user.id) != str(settings.admin_id):
        await message.answer("❌ У вас нет доступа к этой команде")
        return

    await message.answer(
        "⚙️ <b>Админ-панель Barkery</b>\n\n"
        "Выберите раздел для управления:",
        parse_mode="HTML",
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == "admin:back")
async def back_to_admin(callback: CallbackQuery):
    """Возврат в главное меню админки"""
    await admin_entry(callback.message)
    await callback.answer()


@router.callback_query(F.data == "admin_stock")
async def admin_stock_menu(callback: CallbackQuery):
    """Меню управления остатками из админки"""
    await callback.message.edit_text(
        "📊 <b>Управление остатками товаров</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=stock_management_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_backups")
async def admin_backups_menu(callback: CallbackQuery):
    """Меню управления резервными копиями"""
    backups = backup_manager.get_backup_list()

    if not backups:
        text = "📁 <b>Резервные копии</b>\n\nНет созданных резервных копий."
    else:
        text = "📁 <b>Резервные копии базы данных</b>\n\n"
        text += f"Всего копий: {len(backups)}\n"
        text += f"Последняя: {backups[0]['name']}\n"
        text += f"Размер: {backups[0]['size_kb']:.1f} KB\n"
        text += f"Создана: {backups[0]['created'].strftime('%d.%m.%Y %H:%M')}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Создать бэкап сейчас", callback_data="backup:create")],
            [InlineKeyboardButton(text="📋 Список бэкапов", callback_data="backup:list")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back")]
        ]
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()