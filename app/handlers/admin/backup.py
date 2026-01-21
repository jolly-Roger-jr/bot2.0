# app/handlers/admin/backup.py - ИСПРАВЛЕННЫЙ
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from app.config import settings
from app.db.backup import backup_manager, backup_database
from app.scheduler import manual_backup_now

router = Router()


@router.message(Command("backup"))
async def admin_backup_command(message: Message):
    """Команда для создания резервной копии вручную"""
    # Проверка через middleware
    await message.answer("🔄 Создание резервной копии...")

    result = await manual_backup_now()

    if result.get('success'):
        await message.answer(
            f"✅ Резервная копия создана успешно!\n"
            f"Время: {result['timestamp']}\n"
            f"Файл: {result['path']}"
        )
    else:
        await message.answer(
            f"❌ Ошибка при создании резервной копии:\n{result.get('error', 'Неизвестная ошибка')}"
        )


@router.message(Command("backups"))
async def list_backups_command(message: Message):
    """Команда для просмотра списка резервных копий"""
    # Проверка через middleware
    backups = backup_manager.get_backup_list()

    if not backups:
        await message.answer("📁 Резервные копии не найдены")
        return

    text = "📁 *Список резервных копий:*\n\n"
    for i, backup in enumerate(backups[:10], 1):
        size = f"{backup['size_kb']:.1f} KB"
        created = backup['created'].strftime("%d.%m.%Y %H:%M")
        text += f"{i}. *{backup['name']}*\n"
        text += f"   Размер: {size}\n"
        text += f"   Создана: {created}\n\n"

    if len(backups) > 10:
        text += f"\n... и еще {len(backups) - 10} копий"

    await message.answer(text, parse_mode="Markdown")


@router.callback_query(F.data == "backup:create")
async def create_backup_callback(callback: CallbackQuery):
    """Создание резервной копии через callback"""
    # Проверка через middleware
    await callback.answer("🔄 Создание резервной копии...", show_alert=False)

    result = await manual_backup_now()

    if result.get('success'):
        await callback.message.answer(
            f"✅ Резервная копия создана успешно!\n"
            f"Время: {result['timestamp']}\n"
            f"Файл: {result['path']}"
        )
    else:
        await callback.message.answer(
            f"❌ Ошибка при создании резервной копии:\n{result.get('error', 'Неизвестная ошибка')}"
        )

    # Возвращаемся в меню бэкапов
    from app.handlers.admin.panel import admin_backups_menu
    await admin_backups_menu(callback)


@router.callback_query(F.data == "backup:list")
async def list_backups_callback(callback: CallbackQuery):
    """Список резервных копий через callback"""
    # Проверка через middleware
    backups = backup_manager.get_backup_list()

    if not backups:
        await callback.message.edit_text(
            "📁 <b>Резервные копии</b>\n\nНет созданных резервных копий.",
            parse_mode="HTML"
        )
        return

    # Показываем в виде инлайн-списка
    buttons = []
    for backup in backups[:10]:
        btn_text = f"{backup['created'].strftime('%d.%m %H:%M')} - {backup['size_kb']:.0f}KB"
        buttons.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"backup:info:{backup['name']}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_backups")])

    text = f"📁 <b>Резервные копии</b>\n\nВсего: {len(backups)} копий\n"
    if len(backups) > 10:
        text += f"Показаны последние 10\n"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()