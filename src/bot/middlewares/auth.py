from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from src.services.auth_service import auth_service
from src.utils.logger import logger


class AuthMiddleware(BaseMiddleware):
    """Middleware for user authentication"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        """Check if user is authenticated"""

        # Get user from database
        user = await auth_service.get_user_by_telegram_id(event.from_user.id)

        # If user not found and command is not /start, ask to register
        if not user and event.text and not event.text.startswith('/start'):
            await event.answer("Пожалуйста, сначала используйте /start для регистрации")
            return

        # Add user to data
        data['user'] = user

        # Continue processing
        return await handler(event, data)
