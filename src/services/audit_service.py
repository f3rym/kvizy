import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from src.core.database import db
from src.utils.logger import logger


class AuditService:
    """Service for audit logging"""

    async def log_action(
        self,
        user_id: int,
        action: str,
        details: Optional[str] = None,
        success: bool = True
    ) -> bool:
        """
        Log user action to audit log

        Args:
            user_id: User ID
            action: Action name (e.g., 'file_create', 'api_key_add')
            details: Additional details (JSON string or text)
            success: Whether action was successful

        Returns:
            True if logged successfully
        """
        try:
            query = """
                INSERT INTO audit_logs (user_id, action, details, success, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """
            await db.execute(
                query,
                user_id,
                action,
                details,
                success,
                datetime.now()
            )

            logger.info(f"Audit log: user={user_id} action={action} success={success}")
            return True

        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
            return False

    async def get_user_logs(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get audit logs for a user

        Args:
            user_id: User ID
            limit: Maximum number of logs
            offset: Offset for pagination

        Returns:
            List of audit log dicts
        """
        try:
            query = """
                SELECT id, user_id, action, details, success, created_at
                FROM audit_logs
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
            """
            rows = await db.fetch(query, user_id, limit, offset)

            logs = []
            for row in rows:
                logs.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'action': row['action'],
                    'details': row['details'],
                    'success': row['success'],
                    'created_at': row['created_at']
                })

            return logs

        except Exception as e:
            logger.error(f"Error getting user logs: {e}")
            return []

    async def get_all_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all audit logs (admin only)

        Args:
            limit: Maximum number of logs
            offset: Offset for pagination
            action_filter: Filter by action name

        Returns:
            List of audit log dicts with user info
        """
        try:
            if action_filter:
                query = """
                    SELECT
                        al.id, al.user_id, al.action, al.details, al.success, al.created_at,
                        u.username, u.telegram_id
                    FROM audit_logs al
                    JOIN users u ON al.user_id = u.id
                    WHERE al.action = $1
                    ORDER BY al.created_at DESC
                    LIMIT $2 OFFSET $3
                """
                rows = await db.fetch(query, action_filter, limit, offset)
            else:
                query = """
                    SELECT
                        al.id, al.user_id, al.action, al.details, al.success, al.created_at,
                        u.username, u.telegram_id
                    FROM audit_logs al
                    JOIN users u ON al.user_id = u.id
                    ORDER BY al.created_at DESC
                    LIMIT $1 OFFSET $2
                """
                rows = await db.fetch(query, limit, offset)

            logs = []
            for row in rows:
                logs.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'telegram_id': row['telegram_id'],
                    'action': row['action'],
                    'details': row['details'],
                    'success': row['success'],
                    'created_at': row['created_at']
                })

            return logs

        except Exception as e:
            logger.error(f"Error getting all logs: {e}")
            return []

    async def get_action_stats(self) -> Dict:
        """
        Get statistics about actions

        Returns:
            Dict with action counts
        """
        try:
            query = """
                SELECT
                    action,
                    COUNT(*) as count,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failure_count
                FROM audit_logs
                GROUP BY action
                ORDER BY count DESC
            """
            rows = await db.fetch(query)

            stats = {}
            for row in rows:
                stats[row['action']] = {
                    'total': row['count'],
                    'success': row['success_count'],
                    'failure': row['failure_count']
                }

            return stats

        except Exception as e:
            logger.error(f"Error getting action stats: {e}")
            return {}

    async def get_user_stats(self, user_id: int) -> Dict:
        """
        Get statistics for a specific user

        Args:
            user_id: User ID

        Returns:
            Dict with user statistics
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_actions,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failure_count,
                    MIN(created_at) as first_action,
                    MAX(created_at) as last_action
                FROM audit_logs
                WHERE user_id = $1
            """
            row = await db.fetchrow(query, user_id)

            if not row or row['total_actions'] == 0:
                return {
                    'total_actions': 0,
                    'success_count': 0,
                    'failure_count': 0,
                    'first_action': None,
                    'last_action': None
                }

            return {
                'total_actions': row['total_actions'],
                'success_count': row['success_count'],
                'failure_count': row['failure_count'],
                'first_action': row['first_action'],
                'last_action': row['last_action']
            }

        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

    async def search_logs(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search logs by action or details

        Args:
            search_term: Term to search for
            limit: Maximum number of results

        Returns:
            List of matching audit logs
        """
        try:
            query = """
                SELECT
                    al.id, al.user_id, al.action, al.details, al.success, al.created_at,
                    u.username, u.telegram_id
                FROM audit_logs al
                JOIN users u ON al.user_id = u.id
                WHERE al.action ILIKE $1 OR al.details ILIKE $1
                ORDER BY al.created_at DESC
                LIMIT $2
            """
            search_pattern = f"%{search_term}%"
            rows = await db.fetch(query, search_pattern, limit)

            logs = []
            for row in rows:
                logs.append({
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'username': row['username'],
                    'telegram_id': row['telegram_id'],
                    'action': row['action'],
                    'details': row['details'],
                    'success': row['success'],
                    'created_at': row['created_at']
                })

            return logs

        except Exception as e:
            logger.error(f"Error searching logs: {e}")
            return []


# Global audit service instance
audit_service = AuditService()
