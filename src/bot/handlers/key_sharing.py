from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from src.services.key_service import key_service
from src.services.auth_service import auth_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


@router.message(Command("share_key", "sharekey"))
async def share_key_handler(message: Message, user: User):
    """Share API key with another user"""
    # Check if user has a key
    has_key = await key_service.has_key(user.id)
    if not has_key:
        await message.answer("❌ У вас нет API ключа. Сначала добавьте его: /api_key_add")
        return

    # Parse user identifier from command
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "Использование: /share_key <user_id или @username> [примечание]\n\n"
            "Примеры:\n"
            "• /share_key 123456789 Коллега\n"
            "• /share_key @username Тестировщик"
        )
        return

    identifier = parts[1]
    notes = parts[2] if len(parts) > 2 else None

    # Find target user
    target_user = None
    if identifier.startswith('@'):
        username = identifier[1:]
        target_user = await auth_service.get_user_by_username(username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{username} не найден")
            return
    else:
        try:
            telegram_id = int(identifier)
            target_user = await auth_service.get_user_by_telegram_id(telegram_id)
            if not target_user:
                await message.answer(f"❌ Пользователь {telegram_id} не найден")
                return
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте user_id (число) или @username")
            return

    # Can't share with yourself
    if target_user.id == user.id:
        await message.answer("❌ Нельзя поделиться ключом с самим собой")
        return

    # Share the key
    success = await key_service.share_key(user.id, target_user.id, notes)

    if success:
        username_display = f"@{target_user.username}" if target_user.username else f"ID {target_user.telegram_id}"
        await message.answer(
            f"✅ Ключ успешно предоставлен пользователю {username_display}\n\n"
            f"Теперь этот пользователь может использовать ваш API ключ для работы с Claude.\n\n"
            f"Для отзыва доступа используйте: /revoke_key {identifier}"
        )
    else:
        await message.answer("❌ Ошибка при предоставлении доступа")


@router.message(Command("revoke_key", "revokekey"))
async def revoke_key_handler(message: Message, user: User):
    """Revoke shared key access"""
    # Parse user identifier from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Использование: /revoke_key <user_id или @username>\n\n"
            "Примеры:\n"
            "• /revoke_key 123456789\n"
            "• /revoke_key @username"
        )
        return

    identifier = parts[1]

    # Find target user
    target_user = None
    if identifier.startswith('@'):
        username = identifier[1:]
        target_user = await auth_service.get_user_by_username(username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{username} не найден")
            return
    else:
        try:
            telegram_id = int(identifier)
            target_user = await auth_service.get_user_by_telegram_id(telegram_id)
            if not target_user:
                await message.answer(f"❌ Пользователь {telegram_id} не найден")
                return
        except ValueError:
            await message.answer("❌ Неверный формат. Используйте user_id (число) или @username")
            return

    # Revoke access
    success = await key_service.revoke_key(user.id, target_user.id)

    if success:
        username_display = f"@{target_user.username}" if target_user.username else f"ID {target_user.telegram_id}"
        await message.answer(f"✅ Доступ к ключу отозван у пользователя {username_display}")
    else:
        await message.answer("❌ Ошибка при отзыве доступа")


@router.message(Command("my_shares", "myshares"))
async def my_shares_handler(message: Message, user: User):
    """Show who has access to your key and whose key you're using"""
    # Check if user is using someone else's key
    shared_from = await key_service.get_shared_from(user.id)

    # Check who has access to user's key
    shared_with = await key_service.get_shared_with(user.id)

    text = "🔑 Управление доступом к API ключам\n\n"

    if shared_from:
        owner_username = f"@{shared_from['username']}" if shared_from['username'] else f"ID {shared_from['telegram_id']}"
        shared_at = shared_from['shared_at'].strftime('%Y-%m-%d %H:%M')
        text += f"📥 Вы используете ключ пользователя {owner_username}\n"
        text += f"   Предоставлен: {shared_at}\n"
        if shared_from['notes']:
            text += f"   Примечание: {shared_from['notes']}\n"
        text += "\n"
    else:
        has_own_key = await key_service.has_key(user.id)
        if has_own_key:
            text += "🔐 Вы используете свой собственный API ключ\n\n"
        else:
            text += "❌ У вас нет доступа к API ключу\n\n"

    if shared_with:
        text += f"📤 Ваш ключ используют ({len(shared_with)}):\n\n"
        for share in shared_with:
            username = f"@{share['username']}" if share['username'] else f"ID {share['telegram_id']}"
            shared_at = share['shared_at'].strftime('%Y-%m-%d %H:%M')
            text += f"👤 {username}\n"
            text += f"   Предоставлен: {shared_at}\n"
            if share['notes']:
                text += f"   Примечание: {share['notes']}\n"
            text += "\n"
    else:
        text += "📤 Вы не предоставили доступ к своему ключу другим пользователям\n\n"

    text += "Команды:\n"
    text += "• /share_key <user> - предоставить доступ\n"
    text += "• /revoke_key <user> - отозвать доступ"

    await message.answer(text)
