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

    logger.info("Bot started successfully!")


async def on_shutdown():
    """Actions on bot shutdown"""
    logger.info("Shutting down Claude Telegram Bot...")

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

    # TODO: Register handlers here
    # from src.bot.handlers import commands
    # dp.include_router(commands.router)

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
