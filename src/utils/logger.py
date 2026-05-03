import logging
import sys
from pathlib import Path
from src.core.config import settings


def setup_logging():
    """Setup application logging"""

    # Create logs directory if not exists
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(
                log_dir / "bot.log",
                encoding="utf-8"
            )
        ]
    )

    # Set specific loggers
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {settings.log_level}")

    return logger


# Create logger instance
logger = setup_logging()
