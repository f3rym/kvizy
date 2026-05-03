import asyncpg
import asyncio
from typing import Optional
from src.core.config import settings
from src.utils.logger import logger


class Database:
    """Database connection manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self, max_retries: int = 10, retry_delay: int = 3):
        """Create database connection pool with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to database (attempt {attempt + 1}/{max_retries})...")
                self.pool = await asyncpg.create_pool(
                    settings.database_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60,
                    timeout=10
                )
                logger.info("Database connection pool created successfully")
                return
            except Exception as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to database after all retries")
                    raise

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args):
        """Execute a query"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)


# Global database instance
db = Database()
