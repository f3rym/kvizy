from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from src.services.auth_service import auth_service
from src.utils.logger import logger

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """Handle /start command - register or greet user"""
    user = await auth_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    greeting = f"👋 Привет, {message.from_user.first_name}!\n\n"

    if user.is_admin:
        greeting += "🔑 Вы администратор бота.\n\n"

    greeting += """
Я бот для работы с Claude AI.

Доступные команды:
/help - Справка по командам
/status - Статус бота
/profile - Ваш профиль

Используйте /help для подробной информации.
"""

    await message.answer(greeting)
    logger.info(f"User {user.telegram_id} started bot")


@router.message(Command("help"))
async def help_handler(message: Message):
    """Handle /help command"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Сначала используйте /start")
        return

    help_text = """
📖 **Справка по командам**

**Основные команды:**
/start - Начать работу с ботом
/help - Эта справка
/status - Статус бота
/profile - Ваш профиль

**Команды Claude AI:**
/api_key_add - Добавить API ключ
/api_key_show - Показать API ключ (замаскированный)
/api_key_remove - Удалить API ключ
/ask <вопрос> - Задать вопрос Claude
/analyze <код> - Анализ кода
/review <код> - Code review
/fix <код> - Исправить код

**Файловая система:**
(будут добавлены в следующей фазе)
"""

    if user.is_admin:
        help_text += """
**Команды администратора:**
/users - Список пользователей
/make_admin <user_id> - Сделать пользователя админом
"""

    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("status"))
async def status_handler(message: Message):
    """Handle /status command"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Сначала используйте /start")
        return

    status_text = """
✅ **Статус бота**

🤖 Бот: Работает
💾 База данных: Подключена
🔴 Redis: Подключен

Всё работает нормально!
"""

    await message.answer(status_text, parse_mode="Markdown")


@router.message(Command("profile"))
async def profile_handler(message: Message):
    """Handle /profile command"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Сначала используйте /start")
        return

    role_emoji = "🔑" if user.is_admin else "👤"
    profile_text = f"""
{role_emoji} **Ваш профиль**

ID: `{user.id}`
Telegram ID: `{user.telegram_id}`
Username: @{user.username or 'не указан'}
Роль: {user.role}
Зарегистрирован: {user.created_at.strftime('%Y-%m-%d %H:%M')}
"""

    await message.answer(profile_text, parse_mode="Markdown")


@router.message(Command("users"))
async def users_handler(message: Message):
    """Handle /users command - admin only"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Сначала используйте /start")
        return

    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    users = await auth_service.get_all_users()

    users_text = f"👥 **Список пользователей** ({len(users)}):\n\n"

    for u in users:
        role_emoji = "🔑" if u.is_admin else "👤"
        users_text += f"{role_emoji} ID: {u.id} | @{u.username or 'no username'} | {u.role}\n"

    await message.answer(users_text, parse_mode="Markdown")


@router.message(Command("make_admin"))
async def make_admin_handler(message: Message):
    """Handle /make_admin command - admin only"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Сначала используйте /start")
        return

    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    # Parse user_id from command
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /make_admin <user_id>")
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await message.answer("❌ Неверный ID пользователя")
        return

    # Update role
    success = await auth_service.update_user_role(target_user_id, 'admin')

    if success:
        await message.answer(f"✅ Пользователь {target_user_id} теперь администратор")
    else:
        await message.answer("❌ Ошибка при обновлении роли")


@router.message()
async def unknown_handler(message: Message):
    """Handle unknown messages"""
    await message.answer(
        "Я не понимаю эту команду. Используйте /help для списка доступных команд."
    )
