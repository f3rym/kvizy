import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from src.core.config import settings
from src.core.database import db
from src.utils.logger import logger


async def set_bot_commands(bot: Bot):
    """Set bot commands menu"""
    commands = [
        BotCommand(command="start", description="🚀 Начать работу"),
        BotCommand(command="help", description="📖 Справка"),
        BotCommand(command="ask", description="💬 Спросить Claude"),
        BotCommand(command="clear", description="🗑 Очистить историю"),
        BotCommand(command="cron", description="⏰ Добавить cron-задачу"),
        BotCommand(command="reminder", description="⏰ Добавить напоминание"),
        BotCommand(command="cronlist", description="📋 Список задач"),
        BotCommand(command="stats", description="📊 Статистика системы"),
        BotCommand(command="docker", description="🐳 Docker контейнеры"),
        BotCommand(command="profile", description="👤 Мой профиль"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def on_startup():
    """Actions on bot startup"""
    logger.info("Starting Claude Telegram Bot...")

    # Connect to database
    await db.connect()
    logger.info("Database connected")

    # Connect cache service
    from src.services.cache_service import cache_service
    await cache_service.connect()

    # Start scheduler service
    from src.services.scheduler_service import scheduler_service
    scheduler_service.start()

    # Restore scheduled jobs from Redis
    await scheduler_service.restore_jobs()
    logger.info("Scheduler service started")

    logger.info("Bot started successfully!")


async def on_shutdown():
    """Actions on bot shutdown"""
    logger.info("Shutting down Claude Telegram Bot...")

    # Stop scheduler service
    from src.services.scheduler_service import scheduler_service
    scheduler_service.stop()

    # Disconnect cache service
    from src.services.cache_service import cache_service
    await cache_service.disconnect()

    # Disconnect from database
    await db.disconnect()
    logger.info("Database disconnected")

    logger.info("Bot stopped")


async def main():
    """Main bot function"""

    # Initialize bot and dispatcher
    bot = Bot(token=settings.telegram_bot_token)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)

    # Set bot commands menu
    await set_bot_commands(bot)

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register middlewares
    from src.bot.middlewares.auth import AuthMiddleware
    from src.bot.middlewares.audit import AuditMiddleware
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(AuditMiddleware())
    dp.callback_query.middleware(AuthMiddleware())  # Add auth for callbacks

    # Register handlers
    from src.bot.handlers import commands, claude, files, monitor, audit, scheduler, whitelist, key_sharing
    dp.include_router(claude.router)
    dp.include_router(files.router)
    dp.include_router(monitor.router)
    dp.include_router(audit.router)
    dp.include_router(scheduler.router)
    dp.include_router(whitelist.router)
    dp.include_router(key_sharing.router)
    dp.include_router(commands.router)  # Last - contains unknown_handler

    # Set bot instance for scheduler
    from src.services.scheduler_service import scheduler_service
    scheduler_service.set_bot(bot)

    # Start polling
    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error during polling: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
