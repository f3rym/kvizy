from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User model"""
    id: int
    telegram_id: int
    username: Optional[str]
    role: str
    created_at: datetime
    updated_at: datetime

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'

    def __repr__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id}, role={self.role})"
