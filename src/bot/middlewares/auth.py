from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from src.services.auth_service import auth_service
from src.services.whitelist_service import whitelist_service
from src.utils.logger import logger


class AuthMiddleware(BaseMiddleware):
    """Middleware for user authentication and whitelist check"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Check if user is authenticated and whitelisted"""

        telegram_id = event.from_user.id

        # Allow /start command without whitelist check (for first user registration)
        if isinstance(event, Message) and event.text and event.text.startswith('/start'):
            # Get user from database
            user = await auth_service.get_user_by_telegram_id(telegram_id)
            data['user'] = user
            return await handler(event, data)

        # Check whitelist for all other commands
        is_whitelisted = await whitelist_service.is_whitelisted(telegram_id)

        if not is_whitelisted:
            # Not in whitelist - deny access
            if isinstance(event, Message):
                await event.answer(
                    "❌ Доступ запрещен\n\n"
                    "Вы не находитесь в whitelist.\n"
                    "Обратитесь к администратору для получения доступа."
                )
            else:  # CallbackQuery
                await event.answer("❌ Доступ запрещен", show_alert=True)
            logger.warning(f"Access denied for non-whitelisted user: {telegram_id}")
            return

        # Get user from database
        user = await auth_service.get_user_by_telegram_id(telegram_id)

        # If user not found and command is not /start, ask to register
        if not user and isinstance(event, Message) and event.text and not event.text.startswith('/start'):
            await event.answer("Пожалуйста, сначала используйте /start для регистрации")
            return

        # Add user to data
        data['user'] = user

        # Continue processing
        return await handler(event, data)
