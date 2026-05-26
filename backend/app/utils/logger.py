import sys
from loguru import logger
from app.config import get_settings

settings = get_settings()


def setup_logger() -> None:
    logger.remove()

    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level="DEBUG" if settings.debug else "INFO",
        colorize=True,
    )

    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        format=log_format,
        level="INFO",
        rotation="00:00",
        retention="7 days",
        compression="zip",
        encoding="utf-8",
    )


setup_logger()

__all__ = ["logger"]
