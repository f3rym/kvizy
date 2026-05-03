from cryptography.fernet import Fernet
from typing import Optional
from src.core.config import settings
from src.core.database import db
from src.utils.logger import logger


class KeyService:
    """Service for managing encrypted API keys"""

    def __init__(self):
        # Initialize cipher with encryption key from settings
        self.cipher = Fernet(settings.encryption_key.encode())

    async def save_key(self, user_id: int, api_key: str) -> bool:
        """
        Save encrypted API key for user

        Args:
            user_id: User ID
            api_key: Claude API key to encrypt and save

        Returns:
            True if successful
        """
        try:
            # Encrypt the key
            encrypted = self.cipher.encrypt(api_key.encode())

            # Save to database (upsert)
            await db.execute(
                """
                INSERT INTO api_keys (user_id, encrypted_key)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET encrypted_key = $2, created_at = NOW()
                """,
                user_id, encrypted.decode()
            )

            logger.info(f"API key saved for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return False

    async def get_key(self, user_id: int) -> Optional[str]:
        """
        Get decrypted API key for user

        Args:
            user_id: User ID

        Returns:
            Decrypted API key or None if not found
        """
        try:
            row = await db.fetchrow(
                "SELECT encrypted_key FROM api_keys WHERE user_id = $1",
                user_id
            )

            if not row:
                return None

            # Decrypt the key
            encrypted = row['encrypted_key'].encode()
            decrypted = self.cipher.decrypt(encrypted)

            return decrypted.decode()

        except Exception as e:
            logger.error(f"Error getting API key: {e}")
            return None

    async def delete_key(self, user_id: int) -> bool:
        """
        Delete API key for user

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        try:
            await db.execute(
                "DELETE FROM api_keys WHERE user_id = $1",
                user_id
            )

            logger.info(f"API key deleted for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting API key: {e}")
            return False

    async def has_key(self, user_id: int) -> bool:
        """Check if user has API key"""
        count = await db.fetchval(
            "SELECT COUNT(*) FROM api_keys WHERE user_id = $1",
            user_id
        )
        return count > 0

    def mask_key(self, api_key: str) -> str:
        """Mask API key for display (show only first and last 4 chars)"""
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"


# Global key service instance
key_service = KeyService()
