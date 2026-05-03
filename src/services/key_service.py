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

    async def save_key(self, user_id: int, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None) -> bool:
        """
        Save encrypted API key and config for user

        Args:
            user_id: User ID
            api_key: Claude API key to encrypt and save
            base_url: Optional custom base URL
            model: Optional custom model name

        Returns:
            True if successful
        """
        try:
            # Encrypt the key
            encrypted = self.cipher.encrypt(api_key.encode())

            # Save to database (upsert)
            await db.execute(
                """
                INSERT INTO api_keys (user_id, encrypted_key, base_url, model)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET encrypted_key = $2, base_url = $3, model = $4, created_at = NOW()
                """,
                user_id, encrypted.decode(), base_url, model or 'claude-sonnet-4-6'
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

    async def get_config(self, user_id: int) -> Optional[dict]:
        """
        Get full Claude configuration for user
        First checks if user has their own key, then checks if someone shared a key with them

        Args:
            user_id: User ID

        Returns:
            Dict with api_key, base_url, model, is_shared, owner_id or None if not found
        """
        try:
            # First try to get user's own key
            row = await db.fetchrow(
                "SELECT encrypted_key, base_url, model FROM api_keys WHERE user_id = $1",
                user_id
            )

            if row:
                # User has their own key
                encrypted = row['encrypted_key'].encode()
                decrypted = self.cipher.decrypt(encrypted)

                return {
                    'api_key': decrypted.decode(),
                    'base_url': row['base_url'],
                    'model': row['model'] or 'claude-sonnet-4-6',
                    'is_shared': False,
                    'owner_id': user_id
                }

            # Check if someone shared a key with this user
            shared_row = await db.fetchrow(
                """
                SELECT ak.encrypted_key, ak.base_url, ak.model, ks.owner_user_id
                FROM key_sharing ks
                JOIN api_keys ak ON ak.user_id = ks.owner_user_id
                WHERE ks.shared_with_user_id = $1
                LIMIT 1
                """,
                user_id
            )

            if shared_row:
                # User has access to a shared key
                encrypted = shared_row['encrypted_key'].encode()
                decrypted = self.cipher.decrypt(encrypted)

                return {
                    'api_key': decrypted.decode(),
                    'base_url': shared_row['base_url'],
                    'model': shared_row['model'] or 'claude-sonnet-4-6',
                    'is_shared': True,
                    'owner_id': shared_row['owner_user_id']
                }

            return None

        except Exception as e:
            logger.error(f"Error getting config: {e}")
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

    async def share_key(self, owner_user_id: int, shared_with_user_id: int, notes: Optional[str] = None) -> bool:
        """
        Share API key with another user

        Args:
            owner_user_id: User who owns the key
            shared_with_user_id: User to share with
            notes: Optional notes about the sharing

        Returns:
            True if successful
        """
        try:
            # Check if owner has a key
            has_key = await self.has_key(owner_user_id)
            if not has_key:
                logger.warning(f"User {owner_user_id} tried to share key but has none")
                return False

            # Check if already shared
            existing = await db.fetchval(
                "SELECT COUNT(*) FROM key_sharing WHERE owner_user_id = $1 AND shared_with_user_id = $2",
                owner_user_id, shared_with_user_id
            )

            if existing > 0:
                logger.info(f"Key already shared from {owner_user_id} to {shared_with_user_id}")
                return True

            # Share the key
            await db.execute(
                """
                INSERT INTO key_sharing (owner_user_id, shared_with_user_id, notes)
                VALUES ($1, $2, $3)
                """,
                owner_user_id, shared_with_user_id, notes
            )

            logger.info(f"Key shared from user {owner_user_id} to user {shared_with_user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sharing key: {e}")
            return False

    async def revoke_key(self, owner_user_id: int, shared_with_user_id: int) -> bool:
        """
        Revoke shared key access

        Args:
            owner_user_id: User who owns the key
            shared_with_user_id: User to revoke access from

        Returns:
            True if successful
        """
        try:
            result = await db.execute(
                "DELETE FROM key_sharing WHERE owner_user_id = $1 AND shared_with_user_id = $2",
                owner_user_id, shared_with_user_id
            )

            logger.info(f"Key access revoked from user {owner_user_id} to user {shared_with_user_id}")
            return True

        except Exception as e:
            logger.error(f"Error revoking key: {e}")
            return False

    async def get_shared_with(self, owner_user_id: int) -> list:
        """
        Get list of users who have access to owner's key

        Args:
            owner_user_id: User who owns the key

        Returns:
            List of dicts with user info
        """
        try:
            rows = await db.fetch(
                """
                SELECT ks.shared_with_user_id, u.username, u.telegram_id, ks.shared_at, ks.notes
                FROM key_sharing ks
                JOIN users u ON u.id = ks.shared_with_user_id
                WHERE ks.owner_user_id = $1
                ORDER BY ks.shared_at DESC
                """,
                owner_user_id
            )

            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting shared users: {e}")
            return []

    async def get_shared_from(self, user_id: int) -> Optional[dict]:
        """
        Get info about who shared their key with this user

        Args:
            user_id: User ID

        Returns:
            Dict with owner info or None
        """
        try:
            row = await db.fetchrow(
                """
                SELECT ks.owner_user_id, u.username, u.telegram_id, ks.shared_at, ks.notes
                FROM key_sharing ks
                JOIN users u ON u.id = ks.owner_user_id
                WHERE ks.shared_with_user_id = $1
                LIMIT 1
                """,
                user_id
            )

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"Error getting shared from: {e}")
            return None


# Global key service instance
key_service = KeyService()
