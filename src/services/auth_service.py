from typing import Optional
from src.core.database import db
from src.models.user import User
from src.utils.logger import logger


class AuthService:
    """Authentication service"""

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Get existing user or create new one"""

        # Try to get existing user
        user = await self.get_user_by_telegram_id(telegram_id)

        if user:
            logger.info(f"User found: {user}")
            return user

        # Create new user
        logger.info(f"Creating new user: telegram_id={telegram_id}, username={username}")

        # Check if this is the first user (will be admin)
        user_count = await db.fetchval("SELECT COUNT(*) FROM users")
        role = 'admin' if user_count == 0 else 'user'

        row = await db.fetchrow(
            """
            INSERT INTO users (telegram_id, username, role)
            VALUES ($1, $2, $3)
            RETURNING id, telegram_id, username, role, created_at, updated_at
            """,
            telegram_id, username, role
        )

        user = User(**dict(row))
        logger.info(f"User created: {user}")

        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        row = await db.fetchrow(
            "SELECT id, telegram_id, username, role, created_at, updated_at FROM users WHERE telegram_id = $1",
            telegram_id
        )

        if row:
            return User(**dict(row))
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        row = await db.fetchrow(
            "SELECT id, telegram_id, username, role, created_at, updated_at FROM users WHERE id = $1",
            user_id
        )

        if row:
            return User(**dict(row))
        return None

    async def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role"""
        if role not in ['admin', 'user']:
            return False

        await db.execute(
            "UPDATE users SET role = $1, updated_at = NOW() WHERE id = $2",
            role, user_id
        )
        logger.info(f"User {user_id} role updated to {role}")
        return True

    async def get_all_users(self):
        """Get all users"""
        rows = await db.fetch(
            "SELECT id, telegram_id, username, role, created_at, updated_at FROM users ORDER BY created_at DESC"
        )
        return [User(**dict(row)) for row in rows]


# Global auth service instance
auth_service = AuthService()
