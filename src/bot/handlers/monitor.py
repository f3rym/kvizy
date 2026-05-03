from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from src.services.monitor_service import monitor_service
from src.models.user import User
from src.utils.logger import logger

router = Router()


@router.message(Command("stats"))
async def stats_handler(message: Message, user: User):
    """Show system statistics"""
    logger.info(f"Stats handler called by user {user.id}")
    try:
        logger.info("Getting system stats...")
        stats = await monitor_service.get_system_stats()
        logger.info(f"Stats received: {stats}")

        text = f"""
📊 Статистика системы

⏱ Uptime: {stats['uptime']}

🖥 CPU:
• Использование: {stats['cpu']['percent']}%
• Ядер: {stats['cpu']['count']}

💾 Память:
• Использовано: {stats['memory']['used_gb']} GB / {stats['memory']['total_gb']} GB
• Процент: {stats['memory']['percent']}%

💿 Диск:
• Использовано: {stats['disk']['used_gb']} GB / {stats['disk']['total_gb']} GB
• Процент: {stats['disk']['percent']}%

🌐 Сеть:
• Отправлено: {stats['network']['sent_mb']} MB
• Получено: {stats['network']['recv_mb']} MB
"""

        # Check for alerts
        alerts = await monitor_service.check_alerts(stats)
        if alerts:
            text += "\n⚠️ Предупреждения:\n"
            for alert in alerts:
                text += f"• {alert}\n"

        logger.info(f"Sending message with length: {len(text)}")
        try:
            result = await message.answer(text)
            logger.info(f"Message sent successfully, message_id={result.message_id}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Error in stats handler: {e}", exc_info=True)
        await message.answer(f"❌ Ошибка получения статистики: {str(e)}")


@router.message(Command("docker"))
async def docker_handler(message: Message, user: User):
    """Show Docker container statistics"""
    try:
        docker_stats = await monitor_service.get_docker_stats()

        if docker_stats is None:
            await message.answer("❌ Docker недоступен или не установлен")
            return

        text = f"""
🐳 <b>Docker контейнеры</b> ({docker_stats['total_containers']})

"""

        for container in docker_stats['containers']:
            status_emoji = "✅" if container['status'] == 'running' else "❌"
            text += f"""
{status_emoji} <b>{container['name']}</b>
• Статус: {container['status']}
• CPU: {container['cpu_percent']}%
• Memory: {container['memory_mb']} MB ({container['memory_percent']}%)

"""

        await message.answer(text, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка получения Docker статистики: {str(e)}")
        logger.error(f"Error in docker handler: {e}")


@router.message(Command("alerts"))
async def alerts_handler(message: Message, user: User):
    """Show current alert thresholds"""
    thresholds = monitor_service.get_thresholds()

    text = f"""
🔔 <b>Пороги предупреждений</b>

• CPU: {thresholds['cpu_percent']}%
• Memory: {thresholds['memory_percent']}%
• Disk: {thresholds['disk_percent']}%

Используйте /set_alert для изменения порогов.
"""

    await message.answer(text, parse_mode="HTML")


@router.message(Command("set_alert", "setalert"))
async def set_alert_handler(message: Message, user: User):
    """Set alert threshold - admin only"""
    if not user.is_admin:
        await message.answer("❌ Эта команда доступна только администраторам")
        return

    args = message.text.split()

    if len(args) < 3:
        await message.answer(
            "Использование: /set_alert <metric> <value>\n\n"
            "Метрики: cpu_percent, memory_percent, disk_percent\n"
            "Значение: 0-100"
        )
        return

    metric = args[1]
    try:
        value = float(args[2])
    except ValueError:
        await message.answer("❌ Неверное значение. Используйте число от 0 до 100")
        return

    success = monitor_service.set_threshold(metric, value)

    if success:
        await message.answer(f"✅ Порог {metric} установлен на {value}%")
    else:
        await message.answer(
            "❌ Неверная метрика или значение\n\n"
            "Доступные метрики: cpu_percent, memory_percent, disk_percent\n"
            "Значение должно быть от 0 до 100"
        )


@router.message(Command("health"))
async def health_handler(message: Message, user: User):
    """Quick health check"""
    try:
        stats = await monitor_service.get_system_stats()
        alerts = await monitor_service.check_alerts(stats)

        if alerts:
            status = "⚠️ Предупреждения"
            text = f"{status}\n\n"
            for alert in alerts:
                text += f"• {alert}\n"
        else:
            status = "✅ Всё в порядке"
            text = f"{status}\n\n"
            text += f"CPU: {stats['cpu']['percent']}%\n"
            text += f"Memory: {stats['memory']['percent']}%\n"
            text += f"Disk: {stats['disk']['percent']}%\n"

        await message.answer(text)

    except Exception as e:
        await message.answer(f"❌ Ошибка проверки здоровья: {str(e)}")
        logger.error(f"Error in health handler: {e}")
