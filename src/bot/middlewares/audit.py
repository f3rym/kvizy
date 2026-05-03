from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from src.services.audit_service import audit_service
from src.utils.logger import logger


class AuditMiddleware(BaseMiddleware):
    """Middleware to log all user actions"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """
        Log user action before processing

        Args:
            handler: Next handler
            event: Message event
            data: Handler data

        Returns:
            Handler result
        """
        user = data.get('user')

        if not user:
            # No user in context, skip logging
            return await handler(event, data)

        # Extract action from message
        action = None
        details = None
        success = True

        if event.text:
            if event.text.startswith('/'):
                # Command
                parts = event.text.split(maxsplit=1)
                action = f"command:{parts[0][1:]}"  # Remove /
                details = parts[1] if len(parts) > 1 else None
            else:
                # Regular message
                action = "message"
                details = event.text[:100]  # First 100 chars
        elif event.document:
            action = "file_upload"
            details = event.document.file_name
        elif event.photo:
            action = "photo_upload"
        elif event.voice:
            action = "voice_upload"

        try:
            # Process handler
            result = await handler(event, data)
            success = True
        except Exception as e:
            success = False
            logger.error(f"Handler error: {e}")
            raise
        finally:
            # Log action (don't block on logging errors)
            if action:
                try:
                    await audit_service.log_action(
                        user_id=user.id,
                        action=action,
                        details=details,
                        success=success
                    )
                except Exception as e:
                    logger.error(f"Error logging audit action: {e}")

        return result
