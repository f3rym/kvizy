from typing import Optional, List
from src.core.database import db
from src.utils.logger import logger


class WhitelistService:
    """Service for managing whitelist"""

    async def is_whitelisted(self, telegram_id: int) -> bool:
        """Check if user is in whitelist"""
        try:
            query = "SELECT COUNT(*) FROM whitelist WHERE telegram_id = $1"
            count = await db.pool.fetchval(query, telegram_id)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking whitelist: {e}")
            return False

    async def add_to_whitelist(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        added_by: Optional[int] = None,
        notes: Optional[str] = None
    ) -> bool:
        """Add user to whitelist"""
        try:
            query = """
                INSERT INTO whitelist (telegram_id, username, added_by, notes)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_id) DO UPDATE
                SET username = $2, notes = $4
                RETURNING id
            """
            result = await db.pool.fetchval(query, telegram_id, username, added_by, notes)

            # Update user's whitelisted flag
            await db.pool.execute(
                "UPDATE users SET is_whitelisted = TRUE WHERE telegram_id = $1",
                telegram_id
            )

            logger.info(f"Added telegram_id {telegram_id} to whitelist")
            return result is not None
        except Exception as e:
            logger.error(f"Error adding to whitelist: {e}")
            return False

    async def remove_from_whitelist(self, telegram_id: int) -> bool:
        """Remove user from whitelist"""
        try:
            query = "DELETE FROM whitelist WHERE telegram_id = $1 RETURNING id"
            result = await db.pool.fetchval(query, telegram_id)

            # Update user's whitelisted flag
            await db.pool.execute(
                "UPDATE users SET is_whitelisted = FALSE WHERE telegram_id = $1",
                telegram_id
            )

            logger.info(f"Removed telegram_id {telegram_id} from whitelist")
            return result is not None
        except Exception as e:
            logger.error(f"Error removing from whitelist: {e}")
            return False

    async def get_whitelist(self) -> List[dict]:
        """Get all whitelisted users"""
        try:
            query = """
                SELECT w.telegram_id, w.username, w.added_at, w.notes,
                       u.username as added_by_username
                FROM whitelist w
                LEFT JOIN users u ON w.added_by = u.id
                ORDER BY w.added_at DESC
            """
            rows = await db.pool.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting whitelist: {e}")
            return []

    async def get_whitelist_info(self, telegram_id: int) -> Optional[dict]:
        """Get whitelist info for specific user"""
        try:
            query = """
                SELECT w.telegram_id, w.username, w.added_at, w.notes,
                       u.username as added_by_username
                FROM whitelist w
                LEFT JOIN users u ON w.added_by = u.id
                WHERE w.telegram_id = $1
            """
            row = await db.pool.fetchrow(query, telegram_id)
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting whitelist info: {e}")
            return None


# Global whitelist service instance
whitelist_service = WhitelistService()
