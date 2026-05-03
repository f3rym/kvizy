from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.services.whitelist_service import whitelist_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


@router.message(Command("whitelist_add", "whitelistadd"))
async def whitelist_add_handler(message: Message, user: User):
    """Add user to whitelist - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Parse telegram_id or username from command
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "Использование: /whitelist_add <telegram_id или @username> [примечание]\n\n"
            "Примеры:\n"
            "• /whitelist_add 123456789 Разработчик\n"
            "• /whitelist_add @username Тестировщик"
        )
        return

    identifier = parts[1]
    notes = parts[2] if len(parts) > 2 else None

    # Check if it's a username (starts with @)
    if identifier.startswith('@'):
        username = identifier[1:]  # Remove @

        # Try to find user in database by username
        from src.services.auth_service import auth_service
        existing_user = await auth_service.get_user_by_username(username)

        if existing_user:
            telegram_id = existing_user.telegram_id
            await message.answer(f"Найден пользователь: {username} (ID: {telegram_id})")
        else:
            await message.answer(
                f"❌ Пользователь @{username} не найден в базе.\n"
                f"Попросите его написать боту /start, затем добавьте по telegram_id"
            )
            return
    else:
        # It's a telegram_id
        try:
            telegram_id = int(identifier)
            username = None
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте telegram_id (число) или @username")
            return

    success = await whitelist_service.add_to_whitelist(
        telegram_id,
        username=username,
        added_by=user.id,
        notes=notes
    )

    if success:
        await message.answer(
            f"✅ Пользователь добавлен в whitelist\n"
            f"Telegram ID: {telegram_id}\n"
            f"Username: @{username if username else 'нет'}\n"
            f"Примечание: {notes or 'нет'}"
        )
    else:
        await message.answer("❌ Ошибка при добавлении в whitelist")


@router.message(Command("whitelist_remove", "whitelistremove"))
async def whitelist_remove_handler(message: Message, user: User):
    """Remove user from whitelist - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Parse telegram_id from command
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /whitelist_remove <telegram_id>")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный telegram_id")
        return

    success = await whitelist_service.remove_from_whitelist(telegram_id)

    if success:
        await message.answer(f"✅ Пользователь {telegram_id} удален из whitelist")
    else:
        await message.answer(f"❌ Пользователь {telegram_id} не найден в whitelist")


@router.message(Command("whitelist_list", "whitelistlist", "whitelist"))
async def whitelist_list_handler(message: Message, user: User):
    """Show whitelist - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    whitelist = await whitelist_service.get_whitelist()

    if not whitelist:
        await message.answer("📋 Whitelist пуст")
        return

    text = f"📋 Whitelist ({len(whitelist)} пользователей):\n\n"

    for entry in whitelist:
        telegram_id = entry['telegram_id']
        username = entry['username'] or 'нет username'
        added_at = entry['added_at'].strftime('%Y-%m-%d %H:%M')
        notes = entry['notes'] or 'нет'
        added_by = entry['added_by_username'] or 'система'

        text += f"👤 {telegram_id}\n"
        text += f"   Username: @{username}\n" if entry['username'] else f"   Username: {username}\n"
        text += f"   Добавлен: {added_at}\n"
        text += f"   Кем: {added_by}\n"
        text += f"   Примечание: {notes}\n\n"

    await message.answer(text)


@router.message(Command("whitelist_info", "whitelistinfo"))
async def whitelist_info_handler(message: Message, user: User):
    """Show whitelist info for specific user - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Parse telegram_id from command
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /whitelist_info <telegram_id>")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный telegram_id")
        return

    info = await whitelist_service.get_whitelist_info(telegram_id)

    if not info:
        await message.answer(f"❌ Пользователь {telegram_id} не найден в whitelist")
        return

    username = info['username'] or 'нет username'
    added_at = info['added_at'].strftime('%Y-%m-%d %H:%M')
    notes = info['notes'] or 'нет'
    added_by = info['added_by_username'] or 'система'

    text = f"👤 Информация о пользователе {telegram_id}\n\n"
    text += f"Username: @{username}\n" if info['username'] else f"Username: {username}\n"
    text += f"Добавлен: {added_at}\n"
    text += f"Кем: {added_by}\n"
    text += f"Примечание: {notes}"

    await message.answer(text)
