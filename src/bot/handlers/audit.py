from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.services.audit_service import audit_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


@router.message(Command("my_logs", "mylogs"))
async def my_logs_handler(message: Message, user: User):
    """Show user's own audit logs"""
    try:
        logs = await audit_service.get_user_logs(user.id, limit=10)

        if not logs:
            await message.answer("📋 У вас пока нет записей в логах")
            return

        text = f"📋 **Ваши последние действия** (10)\n\n"

        for log in logs:
            status = "✅" if log['success'] else "❌"
            time = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            text += f"{status} `{log['action']}`\n"
            text += f"   {time}\n"
            if log['details']:
                details = log['details'][:50]
                text += f"   {details}\n"
            text += "\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения логов: {str(e)}")
        logger.error(f"Error in my_logs handler: {e}")


@router.message(Command("my_stats", "mystats"))
async def my_stats_handler(message: Message, user: User):
    """Show user's statistics"""
    try:
        stats = await audit_service.get_user_stats(user.id)

        if stats['total_actions'] == 0:
            await message.answer("📊 У вас пока нет статистики")
            return

        text = f"""
📊 **Ваша статистика**

Всего действий: {stats['total_actions']}
✅ Успешных: {stats['success_count']}
❌ Неудачных: {stats['failure_count']}

Первое действие: {stats['first_action'].strftime('%Y-%m-%d %H:%M')}
Последнее действие: {stats['last_action'].strftime('%Y-%m-%d %H:%M')}
"""

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {str(e)}")
        logger.error(f"Error in my_stats handler: {e}")


@router.message(Command("audit_logs", "auditlogs"))
async def audit_logs_handler(message: Message, user: User):
    """Show all audit logs - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    try:
        args = message.text.split()
        limit = 20
        offset = 0

        # Parse pagination
        if len(args) > 1:
            try:
                limit = int(args[1])
                if len(args) > 2:
                    offset = int(args[2])
            except ValueError:
                await message.answer("Использование: /audit_logs [limit] [offset]")
                return

        logs = await audit_service.get_all_logs(limit=limit, offset=offset)

        if not logs:
            await message.answer("📋 Логов не найдено")
            return

        text = f"📋 **Audit Logs** (показано {len(logs)})\n\n"

        for log in logs:
            status = "✅" if log['success'] else "❌"
            time = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            username = log['username'] or f"tg:{log['telegram_id']}"
            text += f"{status} @{username}: `{log['action']}`\n"
            text += f"   {time}\n"
            if log['details']:
                details = log['details'][:40]
                text += f"   {details}\n"
            text += "\n"

        text += f"\nИспользуйте /audit_logs {limit} {offset + limit} для следующей страницы"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения логов: {str(e)}")
        logger.error(f"Error in audit_logs handler: {e}")


@router.message(Command("audit_stats", "auditstats"))
async def audit_stats_handler(message: Message, user: User):
    """Show audit statistics - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    try:
        stats = await audit_service.get_action_stats()

        if not stats:
            await message.answer("📊 Статистики пока нет")
            return

        text = "📊 **Статистика действий**\n\n"

        # Sort by total count
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True)

        for action, counts in sorted_stats[:15]:  # Top 15
            text += f"`{action}`\n"
            text += f"  Всего: {counts['total']} "
            text += f"(✅ {counts['success']} / ❌ {counts['failure']})\n\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения статистики: {str(e)}")
        logger.error(f"Error in audit_stats handler: {e}")


@router.message(Command("audit_search", "auditsearch"))
async def audit_search_handler(message: Message, user: User):
    """Search audit logs - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        await message.answer("Использование: /audit_search <поисковый запрос>")
        return

    search_term = args[1]

    try:
        logs = await audit_service.search_logs(search_term, limit=20)

        if not logs:
            await message.answer(f"🔍 Ничего не найдено по запросу: {search_term}")
            return

        text = f"🔍 **Результаты поиска:** {search_term}\n"
        text += f"Найдено: {len(logs)}\n\n"

        for log in logs:
            status = "✅" if log['success'] else "❌"
            time = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            username = log['username'] or f"tg:{log['telegram_id']}"
            text += f"{status} @{username}: `{log['action']}`\n"
            text += f"   {time}\n"
            if log['details']:
                details = log['details'][:40]
                text += f"   {details}\n"
            text += "\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {str(e)}")
        logger.error(f"Error in audit_search handler: {e}")


@router.message(Command("audit_user", "audituser"))
async def audit_user_handler(message: Message, user: User):
    """Show audit logs for specific user - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    args = message.text.split()

    if len(args) < 2:
        await message.answer("Использование: /audit_user <user_id>")
        return

    try:
        target_user_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID пользователя")
        return

    try:
        # Get user stats
        stats = await audit_service.get_user_stats(target_user_id)

        if stats['total_actions'] == 0:
            await message.answer(f"📊 У пользователя {target_user_id} нет действий")
            return

        # Get recent logs
        logs = await audit_service.get_user_logs(target_user_id, limit=10)

        text = f"📊 **Статистика пользователя {target_user_id}**\n\n"
        text += f"Всего действий: {stats['total_actions']}\n"
        text += f"✅ Успешных: {stats['success_count']}\n"
        text += f"❌ Неудачных: {stats['failure_count']}\n\n"
        text += f"Первое: {stats['first_action'].strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Последнее: {stats['last_action'].strftime('%Y-%m-%d %H:%M')}\n\n"
        text += "**Последние 10 действий:**\n\n"

        for log in logs:
            status = "✅" if log['success'] else "❌"
            time = log['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            text += f"{status} `{log['action']}` - {time}\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения данных: {str(e)}")
        logger.error(f"Error in audit_user handler: {e}")
