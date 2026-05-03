import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from src.core.config import settings
from src.core.database import db
from src.utils.logger import logger


async def on_startup():
    """Actions on bot startup"""
    logger.info("Starting Claude Telegram Bot...")

    # Connect to database
    await db.connect()
    logger.info("Database connected")

    # Connect cache service
    from src.services.cache_service import cache_service
    await cache_service.connect()

    logger.info("Bot started successfully!")


async def on_shutdown():
    """Actions on bot shutdown"""
    logger.info("Shutting down Claude Telegram Bot...")

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

    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register middlewares
    from src.bot.middlewares.auth import AuthMiddleware
    dp.message.middleware(AuthMiddleware())

    # Register handlers
    from src.bot.handlers import commands, claude, files, monitor
    dp.include_router(commands.router)
    dp.include_router(claude.router)
    dp.include_router(files.router)
    dp.include_router(monitor.router)

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
