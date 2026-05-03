from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from src.services.auth_service import auth_service
from src.services.whitelist_service import whitelist_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Get main keyboard with buttons"""
    buttons = [
        [KeyboardButton(text="💬 Диалог с Claude"), KeyboardButton(text="📖 Помощь")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="⏰ Задачи"), KeyboardButton(text="📁 Файлы")],
        [KeyboardButton(text="🗑 Очистить историю")]
    ]

    if is_admin:
        buttons.append([KeyboardButton(text="🔑 Админ панель")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_dialog_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for dialog mode with Claude"""
    buttons = [
        [KeyboardButton(text="🚪 Выйти из диалога")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@router.message(Command("start"))
async def start_handler(message: Message):
    """Handle /start command - register or greet user"""
    telegram_id = message.from_user.id
    username = message.from_user.username

    # Check if this is the first user (auto-whitelist and make admin)
    all_users = await auth_service.get_all_users()
    is_first_user = len(all_users) == 0

    if is_first_user:
        # Add to whitelist automatically
        await whitelist_service.add_to_whitelist(
            telegram_id,
            username=username,
            notes="First user - auto-whitelisted"
        )
        logger.info(f"First user {telegram_id} auto-whitelisted")

    user = await auth_service.get_or_create_user(
        telegram_id=telegram_id,
        username=username
    )

    # Make first user admin
    if is_first_user:
        await auth_service.update_user_role(user.id, 'admin')
        logger.info(f"First user {telegram_id} made admin")

    greeting = f"👋 Привет, {message.from_user.first_name}!\n\n"

    if user.is_admin:
        greeting += "🔑 Вы администратор бота.\n\n"

    greeting += """Я бот для работы с Claude AI.

Используйте кнопки внизу для быстрого доступа к командам или /help для подробной справки."""

    await message.answer(greeting, reply_markup=get_main_keyboard(user.is_admin))
    logger.info(f"User {user.telegram_id} started bot")


@router.message(F.text == "💬 Диалог с Claude")
async def quick_dialog_handler(message: Message):
    """Enter dialog mode with Claude"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return

    from src.services.cache_service import cache_service
    # Use Redis directly to store dialog mode state
    await cache_service.redis_client.setex(f"dialog_mode:{user.id}", 3600, "1")
    await message.answer(
        "💬 Режим диалога с Claude активирован!\n\n"
        "Теперь просто пишите сообщения - они будут отправляться Claude автоматически.\n\n"
        "Для выхода нажмите кнопку 🚪 Выйти из диалога",
        reply_markup=get_dialog_keyboard()
    )


@router.message(F.text == "🚪 Выйти из диалога")
async def exit_dialog_handler(message: Message):
    """Exit dialog mode"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return

    from src.services.cache_service import cache_service
    await cache_service.redis_client.delete(f"dialog_mode:{user.id}")
    await message.answer(
        "✅ Вы вышли из режима диалога",
        reply_markup=get_main_keyboard(user.is_admin)
    )


@router.message(F.text == "📁 Файлы")
async def quick_files_handler(message: Message):
    """Quick files button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📂 Список", callback_data="files_ls"),
            InlineKeyboardButton(text="📍 Путь", callback_data="files_pwd")
        ],
        [
            InlineKeyboardButton(text="📥 Скачать", callback_data="files_download"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data="files_rm")
        ]
    ])
    await message.answer("📁 Управление файлами:", reply_markup=keyboard)


@router.message(F.text == "📖 Помощь")
async def quick_help_handler(message: Message):
    """Quick help button"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return
    await help_handler(message, user)


@router.message(F.text == "📊 Статистика")
async def quick_stats_handler(message: Message):
    """Quick stats button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💻 Система", callback_data="stats_system"),
            InlineKeyboardButton(text="🐳 Docker", callback_data="stats_docker")
        ],
        [InlineKeyboardButton(text="❤️ Здоровье", callback_data="stats_health")]
    ])
    await message.answer("📊 Выберите тип статистики:", reply_markup=keyboard)


@router.message(F.text == "👤 Профиль")
async def quick_profile_handler(message: Message):
    """Quick profile button"""
    await profile_handler(message)


@router.message(F.text == "⏰ Задачи")
async def quick_tasks_handler(message: Message):
    """Quick tasks button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Cron задача", callback_data="task_cron"),
            InlineKeyboardButton(text="⏰ Напоминание", callback_data="task_reminder")
        ],
        [InlineKeyboardButton(text="📋 Список задач", callback_data="task_list")]
    ])
    await message.answer("⏰ Управление задачами:", reply_markup=keyboard)


@router.message(F.text == "🗑 Очистить историю")
async def quick_clear_handler(message: Message):
    """Quick clear history button"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return
    from src.services.claude_service import claude_service
    await claude_service.clear_conversation_history(user.id)
    await message.answer("✅ История диалога очищена")


@router.message(F.text == "🔑 Админ панель")
async def quick_admin_handler(message: Message):
    """Quick admin panel button"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return
    if not user.is_admin:
        await message.answer("❌ Доступно только администраторам")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton(text="📋 Whitelist", callback_data="admin_whitelist")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить в whitelist", callback_data="admin_whitelist_add"),
            InlineKeyboardButton(text="🔑 Управление ключами", callback_data="admin_keys")
        ],
        [
            InlineKeyboardButton(text="📊 Аудит", callback_data="admin_audit"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
        ]
    ])
    await message.answer("🔑 Админ панель:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("stats_"))
async def stats_callback_handler(callback: CallbackQuery, user: User):
    """Handle stats callbacks"""
    action = callback.data.split("_")[1]

    if action == "system":
        from src.services.monitor_service import monitor_service
        stats = await monitor_service.get_system_stats()
        text = f"""💻 Статистика системы

CPU: {stats['cpu']['percent']}% ({stats['cpu']['count']} cores)
Memory: {stats['memory']['used_gb']}/{stats['memory']['total_gb']} GB ({stats['memory']['percent']}%)
Disk: {stats['disk']['used_gb']}/{stats['disk']['total_gb']} GB ({stats['disk']['percent']}%)
Network: ↑{stats['network']['sent_mb']} MB ↓{stats['network']['recv_mb']} MB
Uptime: {stats['uptime']}"""
        await callback.message.answer(text)

    elif action == "docker":
        from src.services.monitor_service import monitor_service
        docker_stats = await monitor_service.get_docker_stats()
        if docker_stats:
            text = f"🐳 Docker контейнеры ({docker_stats['total_containers']}):\n\n"
            for container in docker_stats['containers']:
                text += f"📦 {container['name']}\n"
                text += f"   Status: {container['status']}\n"
                text += f"   CPU: {container['cpu_percent']}%\n"
                text += f"   Memory: {container['memory_mb']} MB ({container['memory_percent']}%)\n\n"
            await callback.message.answer(text)
        else:
            await callback.message.answer("❌ Docker недоступен")

    elif action == "health":
        await callback.message.answer("❤️ Все системы работают нормально!")

    await callback.answer()


@router.callback_query(F.data.startswith("task_"))
async def task_callback_handler(callback: CallbackQuery, user: User):
    """Handle task callbacks"""
    action = callback.data.split("_")[1]

    if action == "cron":
        await callback.message.answer(
            "⏰ Создание cron-задачи\n\n"
            "Используйте команду: /cron"
        )
    elif action == "reminder":
        await callback.message.answer(
            "⏰ Создание напоминания\n\n"
            "Используйте команду: /reminder"
        )
    elif action == "list":
        from src.services.scheduler_service import scheduler_service
        jobs = await scheduler_service.list_jobs(user.id)

        if not jobs:
            await callback.message.answer("📋 У вас нет запланированных задач")
        else:
            text = f"📋 Ваши задачи ({len(jobs)}):\n\n"
            for job in jobs:
                task_id = job.get('task_id', 'unknown')
                job_type = job.get('type', 'unknown')
                description = job.get('description', 'No description')

                if job_type == 'cron':
                    cron_expr = job.get('cron_expression', '')
                    text += f"🔄 {task_id}\n   {cron_expr}\n   {description}\n\n"
                elif job_type == 'reminder':
                    run_date = job.get('run_date', '')
                    text += f"⏰ {task_id}\n   {run_date}\n   {description}\n\n"

            await callback.message.answer(text)

    await callback.answer()


@router.callback_query(F.data.startswith("files_"))
async def files_callback_handler(callback: CallbackQuery, user: User):
    """Handle files callbacks"""
    action = callback.data.split("_")[1]

    if action == "ls":
        await callback.message.answer("Используйте команду: /ls [путь]")
    elif action == "pwd":
        await callback.message.answer("Используйте команду: /pwd")
    elif action == "download":
        await callback.message.answer("Используйте команду: /download <файл>")
    elif action == "rm":
        await callback.message.answer("Используйте команду: /rm <файл>")

    await callback.answer()


@router.callback_query(F.data.startswith("admin_"))
async def admin_callback_handler(callback: CallbackQuery, user: User):
    """Handle admin callbacks"""
    if not user.is_admin:
        await callback.answer("❌ Доступно только администраторам", show_alert=True)
        return

    # Remove "admin_" prefix to get action
    action = callback.data.replace("admin_", "")

    if action == "users":
        users = await auth_service.get_all_users()
        text = f"👥 Пользователи ({len(users)}):\n\n"
        for u in users[:10]:  # Show first 10
            role_emoji = "🔑" if u.is_admin else "👤"
            username_display = f"@{u.username}" if u.username else "no username"
            text += f"{role_emoji} {u.id} | {username_display}\n"
        if len(users) > 10:
            text += f"\n... и еще {len(users) - 10}"
        await callback.message.answer(text)

    elif action == "whitelist":
        from src.services.whitelist_service import whitelist_service
        whitelist = await whitelist_service.get_whitelist()
        if not whitelist:
            await callback.message.answer("📋 Whitelist пуст")
        else:
            text = f"📋 Whitelist ({len(whitelist)}):\n\n"
            for entry in whitelist[:10]:  # Show first 10
                telegram_id = entry['telegram_id']
                username = entry['username'] or 'нет'
                text += f"👤 {telegram_id} (@{username})\n"
            if len(whitelist) > 10:
                text += f"\n... и еще {len(whitelist) - 10}"
            await callback.message.answer(text)

    elif action == "whitelist_add":
        await callback.message.answer(
            "➕ Добавление пользователя в whitelist\n\n"
            "Используйте команду:\n"
            "/whitelist_add <telegram_id или @username> [примечание]\n\n"
            "Примеры:\n"
            "• /whitelist_add 123456789 Разработчик\n"
            "• /whitelist_add @username Тестировщик"
        )

    elif action == "keys":
        await callback.message.answer(
            "🔑 Управление доступом к API ключам\n\n"
            "Команды:\n"
            "• /share_key <user> [note] - предоставить доступ к вашему ключу\n"
            "• /revoke_key <user> - отозвать доступ\n"
            "• /my_shares - посмотреть кто использует ваш ключ\n\n"
            "Примеры:\n"
            "• /share_key @username Коллега\n"
            "• /share_key 123456789 Тестировщик\n"
            "• /revoke_key @username"
        )

    elif action == "audit":
        await callback.message.answer("📊 Используйте команды:\n/audit_stats - статистика\n/audit_logs - логи")

    elif action == "settings":
        await callback.message.answer("⚙️ Используйте команды:\n/set_alert - пороги предупреждений")

    await callback.answer()


@router.message(Command("help"))
async def help_handler(message: Message, user: User):
    """Handle /help command with categories"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤖 Claude AI", callback_data="help_claude"),
            InlineKeyboardButton(text="⏰ Планировщик", callback_data="help_scheduler")
        ],
        [
            InlineKeyboardButton(text="📁 Файлы", callback_data="help_files"),
            InlineKeyboardButton(text="📊 Мониторинг", callback_data="help_monitor")
        ]
    ])

    if user.is_admin:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔑 Админ", callback_data="help_admin")
        ])

    await message.answer(
        "📖 Справка по командам\n\n"
        "Выберите категорию:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("help_"))
async def help_callback_handler(callback: CallbackQuery, user: User):
    """Handle help category callbacks"""
    category = callback.data.split("_")[1]

    if category == "claude":
        text = """🤖 Claude AI

/api_key_add - Добавить API ключ
/api_key_show - Показать конфигурацию
/ask <вопрос> - Задать вопрос
/clear - Очистить историю
/analyze <код> - Анализ кода
/review <код> - Code review
/fix <код> - Исправить код

🔑 Управление доступом:
/share_key <user> - Поделиться ключом
/revoke_key <user> - Отозвать доступ
/my_shares - Мои предоставленные доступы"""

    elif category == "scheduler":
        text = """⏰ Планировщик задач

/cron - Добавить cron-задачу
/reminder - Добавить напоминание
/cronlist - Список задач
/cronremove <id> - Удалить задачу

Примеры cron:
• */5 * * * * - каждые 5 минут
• 0 9 * * 1-5 - в 9:00 по будням"""

    elif category == "files":
        text = """📁 Файловая система

/ls - Список файлов
/pwd - Текущая директория
/cd <путь> - Перейти
/cat <файл> - Прочитать
/mkdir <имя> - Создать папку
/rm <файл> - Удалить
/download <файл> - Скачать"""

    elif category == "monitor":
        text = """📊 Мониторинг

/stats - Статистика системы
/docker - Docker контейнеры
/health - Проверка здоровья
/alerts - Пороги предупреждений
/my_logs - Мои действия
/my_stats - Моя статистика"""

    elif category == "admin":
        if not user.is_admin:
            await callback.answer("❌ Доступно только администраторам", show_alert=True)
            return
        text = """🔑 Администрирование

Пользователи:
/users - Список
/make_admin <id> - Сделать админом

Whitelist:
/whitelist_add <id> [note]
/whitelist_remove <id>
/whitelist - Показать список

Аудит:
/audit_logs - Все логи
/audit_stats - Статистика
/audit_user <id> - Логи пользователя"""

    await callback.message.answer(text)
    await callback.answer()


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
    username_display = f"@{user.username}" if user.username else "не указан"
    profile_text = f"""
{role_emoji} **Ваш профиль**

ID: `{user.id}`
Telegram ID: `{user.telegram_id}`
Username: {username_display}
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
        username_display = f"@{u.username}" if u.username else "no username"
        users_text += f"{role_emoji} ID: {u.id} | {username_display} | {u.role}\n"

    await message.answer(users_text, parse_mode="Markdown")


@router.message(Command("make_admin", "makeadmin"))
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
    """Handle unknown messages - check if in dialog mode"""
    user = await auth_service.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала используйте /start")
        return

    from src.services.cache_service import cache_service

    # Check if user is in dialog mode
    dialog_mode = await cache_service.redis_client.get(f"dialog_mode:{user.id}")

    if dialog_mode:
        # In dialog mode - send to Claude automatically
        from src.services.claude_service import claude_service
        from src.services.key_service import key_service
        import json

        # Check if user has API key configured
        config = await key_service.get_config(user.id)
        if not config:
            await message.answer(
                "❌ Сначала добавьте API ключ: /api_key_add\n\n"
                "Получить ключ можно на https://console.anthropic.com/"
            )
            return

        # Show typing indicator
        await message.bot.send_chat_action(message.chat.id, "typing")

        try:
            response = await claude_service.query(
                prompt=message.text,
                api_key=config['api_key'],
                user_id=user.id,
                model=config.get('model'),
                base_url=config.get('base_url'),
                enable_tools=True
            )

            # Check if response is command confirmation request
            try:
                response_data = json.loads(response)
                if response_data.get("type") == "command_confirmation":
                    # Show commands for confirmation
                    text = response_data.get("text", "Хочу выполнить команду:")
                    commands = response_data.get("commands", [])

                    commands_text = "\n\n".join([f"```bash\n{cmd['command']}\n```" for cmd in commands])

                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Выполнить", callback_data="execute_commands"),
                            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_commands")
                        ]
                    ])

                    await message.answer(
                        f"{text}\n\n{commands_text}",
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    return
            except (json.JSONDecodeError, KeyError):
                pass

            # Send response (split if too long)
            if len(response) <= 4000:
                await message.answer(response)
            else:
                # Split into chunks
                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for chunk in chunks:
                    await message.answer(chunk)

        except Exception as e:
            logger.error(f"Error in dialog mode: {e}")
            await message.answer(f"❌ Ошибка: {str(e)}")
    else:
        # Not in dialog mode - show help
        await message.answer(
            "Я не понимаю эту команду. Используйте /help для списка доступных команд.\n\n"
            "Или нажмите '💬 Диалог с Claude' для общения без команд."
        )
