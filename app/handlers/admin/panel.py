# app/handlers/admin/panel.py - ОБНОВЛЕННЫЙ

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton  # ДОБАВЛЕНО
from app.config import settings
from app.keyboards.admin import admin_menu, stock_management_menu
from app.db.backup import backup_manager

router = Router()


@router.message(F.text == "/admin")
async def admin_entry(message: Message):
    if message.from_user.id != settings.admin_id:
        return
    await message.answer("⚙️ Админ-панель Barkery", reply_markup=admin_menu())


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